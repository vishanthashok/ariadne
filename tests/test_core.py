"""Unit tests for EKF and model forward pass."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from model.architectures.siamese_net import SiameseNet
from model.ekf import VisualInertialEKF
from model.losses.contrastive import InfoNCELoss


def test_ekf_step_predicts_and_updates():
    ekf = VisualInertialEKF(48.4, 38.0, heading0=45.0)
    imu = {"ax": 0.0, "ay": 0.0, "az": 9.81, "gx": 0.0, "gy": 0.0, "gz": 0.01}
    state = ekf.step(imu, visual_estimate=None, visual_confidence=None, dt=0.1)
    assert isinstance(state.lat, float)
    assert state.P.shape == (5, 5)

    before = (state.lat, state.lon)
    state2 = ekf.step(
        imu,
        visual_estimate=(48.401, 38.001),
        visual_confidence=0.9,
        dt=0.1,
    )
    assert state2.lat != before[0] or state2.lon != before[1]
    assert ekf.error_radius_m() > 0


def test_siamese_forward_shape():
    model = SiameseNet(embedding_dim=64)
    # Shrink for speed: replace encoder with tiny stub if needed — still run real forward on small batch
    # Use eval + no grad; ResNet is heavy but one forward is OK for CI smoke
    model.eval()
    x = torch.randn(2, 3, 224, 224)
    with torch.no_grad():
        d, s = model(x, x)
    assert d.shape == (2, 64)
    assert s.shape == (2, 64)
    # L2-normalized
    norms = d.norm(dim=-1)
    assert torch.allclose(norms, torch.ones_like(norms), atol=1e-4)


def test_infonce_loss_runs():
    loss_fn = InfoNCELoss(temperature=0.07)
    a = torch.nn.functional.normalize(torch.randn(4, 32), dim=-1)
    b = torch.nn.functional.normalize(torch.randn(4, 32), dim=-1)
    loss = loss_fn(a, b)
    assert loss.ndim == 0
    assert torch.isfinite(loss)


def test_faiss_query_smoke():
    import faiss

    dim = 32
    xb = np.random.randn(100, dim).astype("float32")
    faiss.normalize_L2(xb)
    index = faiss.IndexFlatIP(dim)
    index.add(xb)
    q = xb[:1].copy()
    scores, idxs = index.search(q, 5)
    assert idxs.shape == (1, 5)
    assert scores[0, 0] > 0.9
