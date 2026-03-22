from __future__ import annotations

import csv
import json
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from time import perf_counter
from typing import Any, Literal, get_args

import torch
from torch import nn
from torch.optim import AdamW, Muon, SGD, Optimizer
from torch.optim.lr_scheduler import CosineAnnealingLR, LRScheduler
from torch.utils.data import DataLoader

from cifar10_speedrun_agentic.data import create_cifar10_dataloaders
from cifar10_speedrun_agentic.models import ModelName, create_cifar10_model

OptimizerName = Literal["sgd", "adamw", "muon"]
SUPPORTED_OPTIMIZERS = get_args(OptimizerName)


class CompositeOptimizer(Optimizer):
    def __init__(self, optimizers: list[Optimizer]) -> None:
        if not optimizers:
            msg = "CompositeOptimizer requires at least one optimizer."
            raise ValueError(msg)

        all_params = [
            param
            for optimizer in optimizers
            for group in optimizer.param_groups
            for param in group["params"]
        ]
        super().__init__(all_params, {})
        self.optimizers = optimizers
        self.param_groups = [
            group for optimizer in optimizers for group in optimizer.param_groups
        ]
        self.state = defaultdict(dict)

    def zero_grad(self, set_to_none: bool = True) -> None:
        for optimizer in self.optimizers:
            optimizer.zero_grad(set_to_none=set_to_none)

    def step(self, closure: Any = None) -> Any:
        loss = None
        for optimizer in self.optimizers:
            current_loss = optimizer.step(closure=closure)
            if current_loss is not None:
                loss = current_loss
        return loss

    def state_dict(self) -> dict[str, Any]:
        return {
            "composite": True,
            "inner_optimizers": [optimizer.state_dict() for optimizer in self.optimizers],
        }

    def load_state_dict(self, state_dict: dict[str, Any]) -> None:
        inner_states = state_dict.get("inner_optimizers", [])
        if len(inner_states) != len(self.optimizers):
            msg = "Composite optimizer state does not match optimizer count."
            raise ValueError(msg)
        for optimizer, optimizer_state in zip(self.optimizers, inner_states, strict=True):
            optimizer.load_state_dict(optimizer_state)


@dataclass(slots=True)
class EpochMetrics:
    loss: float
    accuracy: float
    duration_seconds: float


@dataclass(slots=True)
class TrainingHistory:
    train: list[EpochMetrics] = field(default_factory=list)
    validation: list[EpochMetrics] = field(default_factory=list)
    test: list[EpochMetrics] = field(default_factory=list)


@dataclass(slots=True)
class TrainingArtifacts:
    model: nn.Module
    optimizer: Optimizer
    scheduler: LRScheduler
    history: TrainingHistory
    output_dir: Path


def resolve_device(device: str | torch.device | None = None) -> torch.device:
    if device is not None:
        return torch.device(device)
    if torch.cuda.is_available():
        return torch.device("cuda")
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def create_optimizer(
    model: nn.Module,
    *,
    optimizer_name: OptimizerName,
    learning_rate: float,
    momentum: float,
    weight_decay: float,
) -> Optimizer:
    parameters = [param for param in model.parameters() if param.requires_grad]
    if optimizer_name == "sgd":
        return SGD(
            parameters,
            lr=learning_rate,
            momentum=momentum,
            weight_decay=weight_decay,
        )
    if optimizer_name == "adamw":
        return AdamW(
            parameters,
            lr=learning_rate,
            weight_decay=weight_decay,
        )
    if optimizer_name == "muon":
        muon_params = [param for param in parameters if param.ndim == 2]
        adamw_params = [param for param in parameters if param.ndim != 2]
        optimizers: list[Optimizer] = []
        if muon_params:
            optimizers.append(
                Muon(
                    muon_params,
                    lr=learning_rate,
                    momentum=momentum,
                    weight_decay=weight_decay,
                )
            )
        if adamw_params:
            optimizers.append(
                AdamW(
                    adamw_params,
                    lr=learning_rate,
                    weight_decay=weight_decay,
                )
            )
        if len(optimizers) == 1:
            return optimizers[0]
        return CompositeOptimizer(optimizers)

    msg = (
        f"Unsupported optimizer_name: {optimizer_name}. "
        f"Expected one of {SUPPORTED_OPTIMIZERS}."
    )
    raise ValueError(msg)


def train_one_epoch(
    model: nn.Module,
    dataloader: DataLoader[tuple[torch.Tensor, torch.Tensor | int]],
    optimizer: Optimizer,
    criterion: nn.Module,
    device: torch.device,
    *,
    max_steps: int | None = None,
) -> EpochMetrics:
    model.train()
    total_loss = 0.0
    total_correct = 0
    total_examples = 0
    start = perf_counter()

    for step, batch in enumerate(dataloader, start=1):
        images, targets = batch
        images = images.to(device, non_blocking=True)
        targets = torch.as_tensor(targets, device=device)

        optimizer.zero_grad(set_to_none=True)
        logits = model(images)
        loss = criterion(logits, targets)
        loss.backward()
        optimizer.step()

        batch_size = targets.size(0)
        total_loss += loss.item() * batch_size
        total_correct += (logits.argmax(dim=1) == targets).sum().item()
        total_examples += batch_size

        if max_steps is not None and step >= max_steps:
            break

    return EpochMetrics(
        loss=total_loss / total_examples,
        accuracy=total_correct / total_examples,
        duration_seconds=perf_counter() - start,
    )


@torch.inference_mode()
def evaluate(
    model: nn.Module,
    dataloader: DataLoader[tuple[torch.Tensor, torch.Tensor | int]],
    criterion: nn.Module,
    device: torch.device,
    *,
    max_steps: int | None = None,
) -> EpochMetrics:
    model.eval()
    total_loss = 0.0
    total_correct = 0
    total_examples = 0
    start = perf_counter()

    for step, batch in enumerate(dataloader, start=1):
        images, targets = batch
        images = images.to(device, non_blocking=True)
        targets = torch.as_tensor(targets, device=device)

        logits = model(images)
        loss = criterion(logits, targets)

        batch_size = targets.size(0)
        total_loss += loss.item() * batch_size
        total_correct += (logits.argmax(dim=1) == targets).sum().item()
        total_examples += batch_size

        if max_steps is not None and step >= max_steps:
            break

    return EpochMetrics(
        loss=total_loss / total_examples,
        accuracy=total_correct / total_examples,
        duration_seconds=perf_counter() - start,
    )


def _metrics_to_record(epoch: int, learning_rate: float, metrics: dict[str, EpochMetrics]) -> dict[str, float | int]:
    record: dict[str, float | int] = {"epoch": epoch, "learning_rate": learning_rate}
    for split_name, split_metrics in metrics.items():
        record[f"{split_name}_loss"] = split_metrics.loss
        record[f"{split_name}_accuracy"] = split_metrics.accuracy
        record[f"{split_name}_duration_seconds"] = split_metrics.duration_seconds
    return record


def _write_metrics_record(metrics_path: Path, record: dict[str, float | int]) -> None:
    with metrics_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=True) + "\n")


def _write_history_csv(history_path: Path, records: list[dict[str, float | int]]) -> None:
    if not records:
        return
    fieldnames = list(records[0].keys())
    with history_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)


def _checkpoint_payload(
    epoch: int,
    model: nn.Module,
    optimizer: Optimizer,
    scheduler: LRScheduler,
    history: TrainingHistory,
    metrics_record: dict[str, float | int],
    training_config: dict[str, Any],
) -> dict[str, Any]:
    return {
        "epoch": epoch,
        "model_state_dict": model.state_dict(),
        "optimizer_state_dict": optimizer.state_dict(),
        "scheduler_state_dict": scheduler.state_dict(),
        "history": {
            "train": [asdict(item) for item in history.train],
            "validation": [asdict(item) for item in history.validation],
            "test": [asdict(item) for item in history.test],
        },
        "metrics": metrics_record,
        "training_config": training_config,
    }


def fit(
    model: nn.Module,
    train_loader: DataLoader[tuple[torch.Tensor, torch.Tensor | int]],
    validation_loader: DataLoader[tuple[torch.Tensor, torch.Tensor | int]] | None,
    test_loader: DataLoader[tuple[torch.Tensor, torch.Tensor | int]],
    optimizer: Optimizer,
    criterion: nn.Module,
    device: torch.device,
    *,
    epochs: int,
    scheduler: LRScheduler,
    output_dir: str | Path,
    training_config: dict[str, Any],
    max_train_steps: int | None = None,
    max_eval_steps: int | None = None,
) -> TrainingHistory:
    history = TrainingHistory()
    model.to(device)

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    metrics_path = output_path / "history.jsonl"
    history_csv_path = output_path / "history.csv"
    best_checkpoint_path = output_path / "best_validation.pt"
    latest_checkpoint_path = output_path / "latest.pt"
    best_validation_accuracy = float("-inf")
    records: list[dict[str, float | int]] = []

    metrics_path.write_text("", encoding="utf-8")

    for epoch in range(1, epochs + 1):
        train_metrics = train_one_epoch(
            model,
            train_loader,
            optimizer,
            criterion,
            device,
            max_steps=max_train_steps,
        )

        if validation_loader is not None:
            validation_metrics = evaluate(
                model,
                validation_loader,
                criterion,
                device,
                max_steps=max_eval_steps,
            )
        else:
            validation_metrics = evaluate(
                model,
                test_loader,
                criterion,
                device,
                max_steps=max_eval_steps,
            )

        test_metrics = evaluate(
            model,
            test_loader,
            criterion,
            device,
            max_steps=max_eval_steps,
        )
        learning_rate = optimizer.param_groups[0]["lr"]
        scheduler.step()

        history.train.append(train_metrics)
        history.validation.append(validation_metrics)
        history.test.append(test_metrics)
        metrics_record = _metrics_to_record(
            epoch,
            learning_rate,
            {
                "train": train_metrics,
                "validation": validation_metrics,
                "test": test_metrics,
            },
        )
        records.append(metrics_record)
        _write_metrics_record(metrics_path, metrics_record)
        _write_history_csv(history_csv_path, records)

        checkpoint = _checkpoint_payload(
            epoch,
            model,
            optimizer,
            scheduler,
            history,
            metrics_record,
            training_config,
        )
        torch.save(checkpoint, latest_checkpoint_path)

        if validation_metrics.accuracy >= best_validation_accuracy:
            best_validation_accuracy = validation_metrics.accuracy
            torch.save(checkpoint, best_checkpoint_path)

    return history


def run_training(
    *,
    data_root: str = "data",
    batch_size: int = 128,
    eval_batch_size: int | None = None,
    num_workers: int = 4,
    epochs: int = 10,
    learning_rate: float = 0.1,
    momentum: float = 0.9,
    weight_decay: float = 5e-4,
    optimizer_name: OptimizerName = "sgd",
    label_smoothing: float = 0.0,
    model_name: ModelName = "resnet18",
    device: str | torch.device | None = None,
    output_dir: str | Path = "artifacts",
    validation_split: float = 0.1,
    split_seed: int = 42,
    max_train_steps: int | None = None,
    max_eval_steps: int | None = None,
) -> TrainingArtifacts:
    resolved_device = resolve_device(device)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    loaders = create_cifar10_dataloaders(
        root=data_root,
        batch_size=batch_size,
        eval_batch_size=eval_batch_size,
        num_workers=num_workers,
        pin_memory=resolved_device.type == "cuda",
        validation_split=validation_split,
        split_seed=split_seed,
    )
    model = create_cifar10_model(model_name=model_name)
    criterion = nn.CrossEntropyLoss(label_smoothing=label_smoothing)
    optimizer = create_optimizer(
        model,
        optimizer_name=optimizer_name,
        learning_rate=learning_rate,
        momentum=momentum,
        weight_decay=weight_decay,
    )
    scheduler = CosineAnnealingLR(optimizer, T_max=epochs)
    training_config = {
        "batch_size": batch_size,
        "eval_batch_size": eval_batch_size if eval_batch_size is not None else batch_size,
        "num_workers": num_workers,
        "epochs": epochs,
        "learning_rate": learning_rate,
        "momentum": momentum,
        "weight_decay": weight_decay,
        "optimizer_name": optimizer_name,
        "optimizer_notes": (
            "muon uses Muon for 2D parameters and AdamW for non-2D parameters"
            if optimizer_name == "muon"
            else ""
        ),
        "label_smoothing": label_smoothing,
        "model_name": model_name,
        "validation_split": validation_split,
        "split_seed": split_seed,
    }
    history = fit(
        model,
        loaders.train,
        loaders.validation,
        loaders.test,
        optimizer,
        criterion,
        resolved_device,
        epochs=epochs,
        scheduler=scheduler,
        output_dir=output_path,
        training_config=training_config,
        max_train_steps=max_train_steps,
        max_eval_steps=max_eval_steps,
    )
    return TrainingArtifacts(
        model=model,
        optimizer=optimizer,
        scheduler=scheduler,
        history=history,
        output_dir=output_path,
    )
