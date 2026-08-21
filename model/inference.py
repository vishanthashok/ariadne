"""End-to-end inference: visual geo-localization + EKF fusion."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Optional

import numpy as np
import torch
from PIL import Image
from torchvision import transforms

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from model.architectures.siamese_net import SiameseNet
from model.config import TrainConfig, resolve_device
from model.ekf import VisualInertialEKF

IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]


class AriadneInference:
    def __init__(
        self,
        checkpoint: Path | None = None,
        index_path: Path | None = None,
        coords_path: Path | None = None,
        start_lat: float = 48.4,
        start_lon: float = 38.0,
        confidence_threshold: float = 0.3,
    ):
        self.device = resolve_device("cuda")
        self.confidence_threshold = confidence_threshold
        self.transform = transforms.Compose(
            [
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
            ]
        )
        self.model: Optional[SiameseNet] = None
        self.index = None
        self.mapping: list[dict] = []
        self.ekf = VisualInertialEKF(start_lat, start_lon)
        self.imu_only = VisualInertialEKF(start_lat, start_lon)
        self.loaded = False
        self._try_load(checkpoint, index_path, coords_path)

    def _try_load(self, checkpoint, index_path, coords_path) -> None:
        try:
            import faiss

            ckpt = checkpoint or (ROOT / "model" / "checkpoints" / "best_model.pt")
            idx = index_path or (ROOT / "data" / "faiss_index" / "trained_satellite.index")
            if not idx.exists():
                idx = ROOT / "data" / "faiss_index" / "satellite.index"
            coords = coords_path or (ROOT / "data" / "faiss_index" / "trained_index_to_coords.json")
            if not coords.exists():
                coords = ROOT / "data" / "faiss_index" / "index_to_coords.json"

            if ckpt.exists() and idx.exists() and coords.exists():
                cfg = TrainConfig()
                state = torch.load(ckpt, map_location=self.device, weights_only=False)
                if isinstance(state, dict) and "config" in state:
                    cfg.embedding_dim = state["config"].get("embedding_dim", 512)
                self.model = SiameseNet(embedding_dim=cfg.embedding_dim).to(self.device)
                sd = state["model_state_dict"] if isinstance(state, dict) else state
                self.model.load_state_dict(sd, strict=False)
                self.model.eval()
                self.index = faiss.read_index(str(idx))
                self.mapping = json.loads(coords.read_text())
                self.loaded = True
                print(f"Inference ready: {len(self.mapping)} indexed patches")
            else:
                print("Model/index not found — inference will use heuristic demo mode.")
        except Exception as e:
            print(f"Failed to load inference assets ({e}); heuristic mode.")

    def reset(self, lat: float, lon: float, heading: float = 0.0) -> None:
        self.ekf = VisualInertialEKF(lat, lon, heading0=heading)
        self.imu_only = VisualInertialEKF(lat, lon, heading0=heading)

    @torch.no_grad()
    def process_frame(
        self,
        drone_image: Image.Image | np.ndarray,
        imu_readings: list[dict] | dict,
        true_lat: float | None = None,
        true_lon: float | None = None,
    ) -> dict[str, Any]:
        if isinstance(imu_readings, dict):
            imu_list = [imu_readings]
        else:
            imu_list = list(imu_readings)

        # Always predict with IMU
        for imu in imu_list:
            self.imu_only.predict(imu, dt=0.1)
            self.ekf.predict(imu, dt=0.1)

        visual_est = None
        confidence = 0.0
        top_matches = []

        if self.loaded and self.model is not None and self.index is not None:
            import faiss

            if isinstance(drone_image, np.ndarray):
                img = Image.fromarray(drone_image.astype(np.uint8)).convert("RGB")
            else:
                img = drone_image.convert("RGB")
            x = self.transform(img).unsqueeze(0).to(self.device)
            emb = self.model.encode_drone(x).cpu().numpy().astype(np.float32)
            faiss.normalize_L2(emb)
            scores, idxs = self.index.search(emb, 5)
            for score, idx in zip(scores[0], idxs[0]):
                m = self.mapping[int(idx)]
                top_matches.append(
                    {
                        "satellite_patch_path": m["filename"],
                        "lat": m["lat"],
                        "lon": m["lon"],
                        "similarity_score": float(score),
                    }
                )
            if len(scores[0]) >= 2 and scores[0, 1] > 1e-6:
                confidence = float(scores[0, 0] / (scores[0, 1] + 1e-6))
                confidence = max(0.0, min(1.0, (confidence - 1.0) / 1.0))  # normalize ratio
                # Better: use absolute top-1 as confidence proxy when distinct
                confidence = float(min(1.0, max(0.0, (scores[0, 0] - scores[0, 1] + 0.5))))
            elif len(scores[0]) >= 1:
                confidence = float(min(1.0, max(0.0, scores[0, 0])))

            visual_est = (top_matches[0]["lat"], top_matches[0]["lon"])
            if confidence > self.confidence_threshold:
                self.ekf.update(visual_est[0], visual_est[1], confidence)
        elif true_lat is not None and true_lon is not None:
            # Heuristic demo: noisy visual fix around truth
            noise = np.random.normal(0, 0.002, size=2)
            visual_est = (true_lat + float(noise[0]), true_lon + float(noise[1]))
            confidence = float(np.clip(np.random.uniform(0.4, 0.95), 0, 1))
            top_matches = [
                {
                    "satellite_patch_path": "demo_patch.png",
                    "lat": visual_est[0],
                    "lon": visual_est[1],
                    "similarity_score": confidence,
                }
            ]
            if confidence > self.confidence_threshold:
                self.ekf.update(visual_est[0], visual_est[1], confidence)

        fused = self.ekf.get_state()
        imu_state = self.imu_only.get_state()
        return {
            "estimated_position": {
                "lat": fused.lat,
                "lon": fused.lon,
                "confidence": confidence,
                "error_radius_m": self.ekf.error_radius_m(),
                "source": "fused" if confidence > self.confidence_threshold else "imu",
            },
            "visual_only_position": (
                {
                    "lat": visual_est[0],
                    "lon": visual_est[1],
                    "confidence": confidence,
                    "error_radius_m": 50.0 / max(confidence, 0.1),
                    "source": "visual",
                }
                if visual_est
                else None
            ),
            "imu_only_position": {
                "lat": imu_state.lat,
                "lon": imu_state.lon,
                "confidence": 0.2,
                "error_radius_m": self.imu_only.error_radius_m(),
                "source": "imu",
            },
            "top_matches": top_matches,
            "ekf_state": {
                "x": fused.__dict__ and [fused.lat, fused.lon, fused.vn, fused.ve, fused.heading],
                "P": fused.P.tolist(),
                "heading": fused.heading,
                "vn": fused.vn,
                "ve": fused.ve,
            },
            "confidence": confidence,
        }
