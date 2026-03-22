from __future__ import annotations

from typing import Literal, get_args

import torch.nn as nn
from torchvision.models import resnet18, resnext50_32x4d

ModelName = Literal["resnet18", "resnext50_32x4d"]
SUPPORTED_MODELS = get_args(ModelName)


def _adapt_model_for_cifar10(model: nn.Module) -> nn.Module:
    model.conv1 = nn.Conv2d(
        3,
        64,
        kernel_size=3,
        stride=1,
        padding=1,
        bias=False,
    )
    model.maxpool = nn.Identity()
    return model


def create_cifar10_model(
    model_name: ModelName = "resnet18",
    *,
    num_classes: int = 10,
) -> nn.Module:
    if model_name == "resnet18":
        model = resnet18(weights=None, num_classes=num_classes)
        return _adapt_model_for_cifar10(model)
    if model_name == "resnext50_32x4d":
        model = resnext50_32x4d(weights=None, num_classes=num_classes)
        return _adapt_model_for_cifar10(model)

    msg = f"Unsupported model_name: {model_name}. Expected one of {SUPPORTED_MODELS}."
    raise ValueError(msg)
