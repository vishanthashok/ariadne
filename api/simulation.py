"""Flight simulation engine — replays IMU + drone views through inference."""

from __future__ import annotations

import base64
import csv
import io
import math
import sys
import time
from pathlib import Path
from typing import Any, Optional

import numpy as np
from PIL import Image, ImageEnhance

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from api.schemas import FrameResponse, MatchResult, PositionEstimate, SimulationConfig
from model.inference import AriadneInference


def haversine_m(lat1, lon1, lat2, lon2) -> float:
    r = 6_371_000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


class SimulationEngine:
    def __init__(self, config: Optional[SimulationConfig] = None):
        self.config = config or SimulationConfig()
        self.running = False
        self.paused = False
        self.frame_idx = 0
        self.imu_rows: list[dict] = []
        self.drone_images: list[Path] = []
        self.inference = AriadneInference()
        self.confidence_history: list[float] = []
        self.error_history: list[float] = []
        self.fix_count = 0
        self.start_time = 0.0
        self._load_flight(self.config.flight_id)

    def _load_flight(self, flight_id: int) -> None:
        imu_path = ROOT / "data" / "processed" / "imu_data" / f"flight_{flight_id}.csv"
        if not imu_path.exists():
            # Generate a lightweight in-memory synthetic flight
            self.imu_rows = self._synthetic_imu()
        else:
            with imu_path.open(encoding="utf-8") as f:
                self.imu_rows = list(csv.DictReader(f))

        # Sample visual frames at 2 Hz from 10 Hz IMU (every 5th row)
        self.visual_indices = list(range(0, len(self.imu_rows), 5))
        patches = sorted((ROOT / "data" / "processed" / "drone_views").glob("drone_*.png"))
        self.drone_images = patches
        if self.imu_rows:
            r0 = self.imu_rows[0]
            self.inference.reset(float(r0["true_lat"]), float(r0["true_lon"]), float(r0.get("true_heading", 0)))

    def _synthetic_imu(self, n: int = 3000) -> list[dict]:
        rows = []
        lat, lon = 48.4, 38.0
        heading = 45.0
        speed = 12.0
        for i in range(n):
            t = i * 0.1
            heading += math.sin(t / 40) * 0.3
            dn = speed * math.cos(math.radians(heading)) * 0.1
            de = speed * math.sin(math.radians(heading)) * 0.1
            lat += dn / 111_320
            lon += de / (111_320 * math.cos(math.radians(lat)))
            rows.append(
                {
                    "timestamp": t,
                    "ax": 0.0,
                    "ay": 0.0,
                    "az": 9.81,
                    "gx": 0.0,
                    "gy": 0.0,
                    "gz": math.radians(0.3),
                    "true_lat": lat,
                    "true_lon": lon,
                    "true_alt": self.config.altitude_m,
                    "true_heading": heading,
                    "true_speed": speed,
                }
            )
        return rows

    def start(self) -> None:
        self.running = True
        self.paused = False
        self.start_time = time.time()

    def stop(self) -> None:
        self.running = False

    def restart(self) -> None:
        self.frame_idx = 0
        self.confidence_history = []
        self.error_history = []
        self.fix_count = 0
        self._load_flight(self.config.flight_id)
        self.start()

    def apply_control(self, action: str, value: Any = None) -> None:
        if action == "set_speed":
            self.config.speed = float(value)
        elif action == "toggle_jamming":
            self.config.gps_jammed = not self.config.gps_jammed if value is None else bool(value)
        elif action == "set_noise":
            self.config.camera_noise = float(value)
        elif action == "set_altitude":
            self.config.altitude_m = float(value)
        elif action == "pause":
            self.paused = True
        elif action == "play":
            self.paused = False
            self.running = True
        elif action == "restart":
            self.restart()

    def _get_drone_image(self, idx: int) -> Image.Image:
        if self.drone_images:
            path = self.drone_images[idx % len(self.drone_images)]
            img = Image.open(path).convert("RGB")
        else:
            # Synthetic colored noise frame
            arr = np.random.randint(40, 120, (256, 256, 3), dtype=np.uint8)
            img = Image.fromarray(arr)
        if self.config.camera_noise > 0:
            arr = np.array(img).astype(np.float32)
            noise = np.random.normal(0, 40 * self.config.camera_noise, arr.shape)
            arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
            img = Image.fromarray(arr)
            img = ImageEnhance.Contrast(img).enhance(1.0 - 0.4 * self.config.camera_noise)
        return img

    def _img_b64(self, img: Image.Image) -> str:
        buf = io.BytesIO()
        img.resize((256, 256)).save(buf, format="JPEG", quality=70)
        return base64.b64encode(buf.getvalue()).decode("ascii")

    def step(self) -> Optional[FrameResponse]:
        if self.paused:
            return None
        if self.frame_idx >= len(self.visual_indices):
            self.running = False
            return None

        v_idx = self.visual_indices[self.frame_idx]
        # IMU batch since last visual frame
        start_imu = self.visual_indices[self.frame_idx - 1] + 1 if self.frame_idx > 0 else 0
        imu_batch = []
        for i in range(start_imu, v_idx + 1):
            row = self.imu_rows[i]
            imu_batch.append(
                {
                    "ax": float(row["ax"]),
                    "ay": float(row["ay"]),
                    "az": float(row["az"]),
                    "gx": float(row["gx"]),
                    "gy": float(row["gy"]),
                    "gz": float(row["gz"]),
                }
            )
        row = self.imu_rows[v_idx]
        true_lat, true_lon = float(row["true_lat"]), float(row["true_lon"])
        img = self._get_drone_image(self.frame_idx)

        # If GPS not jammed, inject perfect GPS as high-confidence visual
        result = self.inference.process_frame(img, imu_batch, true_lat=true_lat, true_lon=true_lon)
        if not self.config.gps_jammed:
            # Snap to GPS truth
            self.inference.ekf.update(true_lat, true_lon, 0.99)
            result["estimated_position"] = {
                "lat": true_lat,
                "lon": true_lon,
                "confidence": 1.0,
                "error_radius_m": 5.0,
                "source": "gps",
            }
            result["confidence"] = 1.0
            mode = "GPS"
        else:
            mode = "VISUAL-INERTIAL" if result["confidence"] > 0.3 else "IMU ONLY"

        est = result["estimated_position"]
        err = haversine_m(true_lat, true_lon, est["lat"], est["lon"])
        imu_err = haversine_m(
            true_lat,
            true_lon,
            result["imu_only_position"]["lat"],
            result["imu_only_position"]["lon"],
        )
        conf = float(result["confidence"])
        if conf > 0.3 and self.config.gps_jammed:
            self.fix_count += 1
        self.confidence_history.append(conf)
        self.error_history.append(err)

        visual = result.get("visual_only_position")
        frame = FrameResponse(
            timestamp=float(row["timestamp"]),
            estimated_position=PositionEstimate(**est),
            ground_truth=PositionEstimate(
                lat=true_lat,
                lon=true_lon,
                confidence=1.0,
                error_radius_m=0.0,
                source="truth",
            ),
            top_matches=[MatchResult(**m) for m in result.get("top_matches", [])[:5]],
            imu_only_position=PositionEstimate(**result["imu_only_position"]),
            visual_only_position=PositionEstimate(**visual) if visual else None,
            ekf_state=result.get("ekf_state", {}),
            metrics={
                "error_m": err,
                "imu_error_m": imu_err,
                "drift_m": imu_err,
                "confidence_history": self.confidence_history[-50:],
                "frames": self.frame_idx + 1,
                "fixes": self.fix_count,
                "avg_error": float(np.mean(self.error_history)) if self.error_history else 0.0,
                "max_drift": float(np.max([e for e in self.error_history] or [0])),
                "fix_rate": self.fix_count / max(1, self.frame_idx + 1),
                "runtime": float(row["timestamp"]),
                "visual_fix": conf > 0.3,
            },
            drone_image_b64=self._img_b64(img),
            altitude_m=float(row.get("true_alt", self.config.altitude_m)),
            heading=float(row.get("true_heading", 0)),
            speed_mps=float(row.get("true_speed", 12)),
            gps_jammed=self.config.gps_jammed,
            mode=mode,
        )
        self.frame_idx += 1
        return frame

    def get_state(self) -> dict:
        return {
            "running": self.running,
            "paused": self.paused,
            "frame_idx": self.frame_idx,
            "total_frames": len(self.visual_indices),
            "config": self.config.model_dump(),
        }

    def run_all(self, max_frames: int = 1000) -> list[dict]:
        self.restart()
        frames = []
        while self.frame_idx < len(self.visual_indices) and len(frames) < max_frames:
            fr = self.step()
            if fr is None:
                break
            frames.append(fr.model_dump())
        return frames
