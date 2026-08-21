"""Shared ResNet-50 feature extractor with projection head."""

from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import models


class FeatureExtractor(nn.Module):
    def __init__(self, embedding_dim: int = 512, freeze_early: bool = True):
        super().__init__()
        weights = models.ResNet50_Weights.IMAGENET1K_V2
        backbone = models.resnet50(weights=weights)
        # Remove FC
        self.backbone = nn.Sequential(*list(backbone.children())[:-1])  # -> (B, 2048, 1, 1)

        if freeze_early:
            # Freeze first 6 children of original resnet (conv1..layer2 roughly)
            children = list(backbone.children())
            for i, child in enumerate(children):
                if i < 6:
                    for p in child.parameters():
                        p.requires_grad = False

        self.projection = nn.Sequential(
            nn.Linear(2048, 512),
            nn.BatchNorm1d(512),
            nn.ReLU(inplace=True),
            nn.Linear(512, embedding_dim),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        feats = self.backbone(x).flatten(1)
        emb = self.projection(feats)
        return F.normalize(emb, dim=-1)
