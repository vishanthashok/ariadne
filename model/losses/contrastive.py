"""Contrastive losses: InfoNCE and Triplet."""

from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F


class InfoNCELoss(nn.Module):
    def __init__(self, temperature: float = 0.07):
        super().__init__()
        self.temperature = temperature

    def forward(self, drone_emb: torch.Tensor, sat_emb: torch.Tensor) -> torch.Tensor:
        # (B, D) @ (D, B) -> (B, B)
        sim = drone_emb @ sat_emb.T / self.temperature
        labels = torch.arange(sim.size(0), device=sim.device)
        return F.cross_entropy(sim, labels)


class TripletLoss(nn.Module):
    def __init__(self, margin: float = 0.5):
        super().__init__()
        self.margin = margin

    def forward(
        self,
        anchor: torch.Tensor,
        positive: torch.Tensor,
        negative: torch.Tensor,
    ) -> torch.Tensor:
        d_pos = torch.sum((anchor - positive) ** 2, dim=-1)
        d_neg = torch.sum((anchor - negative) ** 2, dim=-1)
        loss = torch.clamp(d_pos - d_neg + self.margin, min=0.0)
        return loss.mean()
