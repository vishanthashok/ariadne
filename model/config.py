"""Training and inference configuration."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class TrainConfig:
    backbone: str = "resnet50"
    embedding_dim: int = 512
    image_size: int = 224
    batch_size: int = 64
    num_epochs: int = 50
    learning_rate: float = 3e-4
    weight_decay: float = 1e-4
    temperature: float = 0.07
    num_negatives: int = 5
    margin: float = 0.5
    loss_type: str = "infonce"
    train_split: float = 0.8
    val_split: float = 0.1
    test_split: float = 0.1
    checkpoint_dir: str = "model/checkpoints"
    device: str = "cuda"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def resolve_device(preferred: str = "cuda") -> str:
    import torch

    if preferred == "cuda" and torch.cuda.is_available():
        return "cuda"
    return "cpu"
