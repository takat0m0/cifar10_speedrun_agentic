from __future__ import annotations

import argparse

from cifar10_speedrun_agentic.train import run_training


def main() -> None:
    parser = argparse.ArgumentParser(description="Train a CIFAR-10 model.")
    parser.add_argument("--data-root", default="data")
    parser.add_argument("--output-dir", default="artifacts")
    parser.add_argument("--batch-size", type=int, default=128)
    parser.add_argument("--eval-batch-size", type=int, default=None)
    parser.add_argument("--num-workers", type=int, default=4)
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--learning-rate", type=float, default=0.1)
    parser.add_argument("--momentum", type=float, default=0.9)
    parser.add_argument("--weight-decay", type=float, default=5e-4)
    parser.add_argument("--optimizer-name", choices=("sgd", "adamw", "muon"), default="sgd")
    parser.add_argument("--label-smoothing", type=float, default=0.0)
    parser.add_argument("--model-name", choices=("resnet18", "resnext50_32x4d"), default="resnet18")
    parser.add_argument("--validation-split", type=float, default=0.1)
    parser.add_argument("--split-seed", type=int, default=42)
    parser.add_argument("--device", default=None)
    parser.add_argument("--max-train-steps", type=int, default=None)
    parser.add_argument("--max-eval-steps", type=int, default=None)
    args = parser.parse_args()

    artifacts = run_training(
        data_root=args.data_root,
        batch_size=args.batch_size,
        eval_batch_size=args.eval_batch_size,
        num_workers=args.num_workers,
        epochs=args.epochs,
        learning_rate=args.learning_rate,
        momentum=args.momentum,
        weight_decay=args.weight_decay,
        optimizer_name=args.optimizer_name,
        label_smoothing=args.label_smoothing,
        model_name=args.model_name,
        device=args.device,
        output_dir=args.output_dir,
        validation_split=args.validation_split,
        split_seed=args.split_seed,
        max_train_steps=args.max_train_steps,
        max_eval_steps=args.max_eval_steps,
    )

    for epoch, (train_metrics, validation_metrics, test_metrics) in enumerate(
        zip(
            artifacts.history.train,
            artifacts.history.validation,
            artifacts.history.test,
        ),
        start=1,
    ):
        print(
            f"epoch={epoch} "
            f"train_acc={train_metrics.accuracy:.4f} "
            f"validation_acc={validation_metrics.accuracy:.4f} "
            f"test_acc={test_metrics.accuracy:.4f} "
            f"output_dir={artifacts.output_dir}"
        )


if __name__ == "__main__":
    main()
