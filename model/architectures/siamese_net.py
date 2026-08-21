"""Siamese network with shared feature extractor."""

from __future__ import annotations

import torch
import torch.nn as nn

from .feature_extractor import FeatureExtractor


class SiameseNet(nn.Module):
    def __init__(self, embedding_dim: int = 512):
        super().__init__()
        self.encoder = FeatureExtractor(embedding_dim=embedding_dim)

    def forward(self, drone_image: torch.Tensor, satellite_image: torch.Tensor):
        return self.encoder(drone_image), self.encoder(satellite_image)

    def encode_drone(self, image: torch.Tensor) -> torch.Tensor:
        return self.encoder(image)

    def encode_satellite(self, image: torch.Tensor) -> torch.Tensor:
        return self.encoder(image)
