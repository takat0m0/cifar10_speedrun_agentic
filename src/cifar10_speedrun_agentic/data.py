from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import torch
from torch.utils.data import DataLoader, Subset
from torchvision import datasets, transforms

CIFAR10_MEAN = (0.4914, 0.4822, 0.4465)
CIFAR10_STD = (0.2470, 0.2435, 0.2616)


@dataclass(slots=True)
class Cifar10DataLoaders:
    train: DataLoader[tuple[torch.Tensor, int]]
    validation: DataLoader[tuple[torch.Tensor, int]] | None
    test: DataLoader[tuple[torch.Tensor, int]]


def default_train_transform() -> transforms.Compose:
    return transforms.Compose(
        [
            transforms.RandomCrop(32, padding=4),
            transforms.RandomHorizontalFlip(),
            transforms.ToTensor(),
            transforms.Normalize(CIFAR10_MEAN, CIFAR10_STD),
        ]
    )


def default_test_transform() -> transforms.Compose:
    return transforms.Compose(
        [
            transforms.ToTensor(),
            transforms.Normalize(CIFAR10_MEAN, CIFAR10_STD),
        ]
    )


def download_cifar10(
    root: str | Path = "data",
    *,
    train_transform: transforms.Compose | None = None,
    test_transform: transforms.Compose | None = None,
) -> tuple[datasets.CIFAR10, datasets.CIFAR10]:
    data_root = Path(root)
    data_root.mkdir(parents=True, exist_ok=True)

    train_dataset = datasets.CIFAR10(
        root=data_root,
        train=True,
        download=True,
        transform=train_transform or default_train_transform(),
    )
    test_dataset = datasets.CIFAR10(
        root=data_root,
        train=False,
        download=True,
        transform=test_transform or default_test_transform(),
    )
    return train_dataset, test_dataset


def create_cifar10_dataloaders(
    root: str | Path = "data",
    *,
    batch_size: int = 128,
    eval_batch_size: int | None = None,
    num_workers: int = 4,
    pin_memory: bool = True,
    persistent_workers: bool | None = None,
    train_transform: transforms.Compose | None = None,
    test_transform: transforms.Compose | None = None,
    validation_split: float = 0.0,
    split_seed: int = 42,
) -> Cifar10DataLoaders:
    effective_eval_batch_size = eval_batch_size or batch_size
    use_persistent_workers = (
        persistent_workers if persistent_workers is not None else num_workers > 0
    )
    data_root = Path(root)
    data_root.mkdir(parents=True, exist_ok=True)

    train_dataset = datasets.CIFAR10(
        root=data_root,
        train=True,
        download=True,
        transform=train_transform or default_train_transform(),
    )
    test_dataset = datasets.CIFAR10(
        root=data_root,
        train=False,
        download=True,
        transform=test_transform or default_test_transform(),
    )

    validation_loader: DataLoader[tuple[torch.Tensor, int]] | None = None
    train_source: torch.utils.data.Dataset[tuple[torch.Tensor, int]] = train_dataset

    if not 0.0 <= validation_split < 1.0:
        msg = "validation_split must be in the range [0.0, 1.0)."
        raise ValueError(msg)

    if validation_split > 0.0:
        validation_dataset = datasets.CIFAR10(
            root=data_root,
            train=True,
            download=True,
            transform=test_transform or default_test_transform(),
        )
        generator = torch.Generator().manual_seed(split_seed)
        permutation = torch.randperm(len(train_dataset), generator=generator).tolist()
        validation_size = int(len(train_dataset) * validation_split)
        if validation_size == 0:
            msg = "validation_split is too small and produced an empty validation set."
            raise ValueError(msg)
        validation_indices = permutation[:validation_size]
        train_indices = permutation[validation_size:]
        train_source = Subset(train_dataset, train_indices)
        validation_source = Subset(validation_dataset, validation_indices)
        validation_loader = DataLoader(
            validation_source,
            batch_size=effective_eval_batch_size,
            shuffle=False,
            num_workers=num_workers,
            pin_memory=pin_memory,
            persistent_workers=use_persistent_workers,
        )

    train_loader = DataLoader(
        train_source,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        pin_memory=pin_memory,
        persistent_workers=use_persistent_workers,
    )
    test_loader = DataLoader(
        test_dataset,
        batch_size=effective_eval_batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=pin_memory,
        persistent_workers=use_persistent_workers,
    )
    return Cifar10DataLoaders(
        train=train_loader,
        validation=validation_loader,
        test=test_loader,
    )
