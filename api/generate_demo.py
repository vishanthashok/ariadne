"""Generate pre-recorded demo JSON for frontend fallback mode."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def generate_demo_frames(n: int = 1000) -> list[dict]:
    """Deterministic demo trajectory — no model required."""
    rng = np.random.default_rng(42)
    frames = []
    lat, lon = 48.40, 37.95
    heading = 40.0
    speed = 12.0
    imu_lat, imu_lon = lat, lon
    fused_lat, fused_lon = lat, lon
    fixes = 0
    errors = []

    for i in range(n):
        t = i * 0.5
        heading += math.sin(t / 30) * 0.8
        dn = speed * math.cos(math.radians(heading)) * 0.5
        de = speed * math.sin(math.radians(heading)) * 0.5
        lat += dn / 111_320
        lon += de / (111_320 * math.cos(math.radians(lat)))

        # IMU drifts
        imu_bias_n = 0.4 + 0.02 * t
        imu_bias_e = 0.3 + 0.015 * t
        imu_lat += (dn + imu_bias_n) / 111_320
        imu_lon += (de + imu_bias_e) / (111_320 * math.cos(math.radians(lat)))

        # Visual fix every ~8 frames with noise
        confidence = float(np.clip(0.55 + 0.35 * math.sin(t / 8) + rng.normal(0, 0.05), 0.05, 0.98))
        visual_fix = confidence > 0.3 and (i % 8 != 0 or confidence > 0.7)
        if i % 8 == 3:
            confidence = float(rng.uniform(0.1, 0.25))  # occasional reject
            visual_fix = False

        if visual_fix:
            fixes += 1
            v_lat = lat + float(rng.normal(0, 0.0004))
            v_lon = lon + float(rng.normal(0, 0.0004))
            # snap fused toward visual
            fused_lat = 0.7 * v_lat + 0.3 * fused_lat
            fused_lon = 0.7 * v_lon + 0.3 * fused_lon
            source = "fused"
            mode = "VISUAL-INERTIAL"
            err_radius = 50 + (1 - confidence) * 200
        else:
            fused_lat += (dn + 0.15) / 111_320
            fused_lon += (de + 0.1) / (111_320 * math.cos(math.radians(lat)))
            source = "imu"
            mode = "IMU ONLY"
            err_radius = 200 + 3 * (i % 8)
            v_lat, v_lon = fused_lat, fused_lon

        err = math.hypot((fused_lat - lat) * 111_320, (fused_lon - lon) * 111_320 * math.cos(math.radians(lat)))
        imu_err = math.hypot((imu_lat - lat) * 111_320, (imu_lon - lon) * 111_320 * math.cos(math.radians(lat)))
        errors.append(err)

        # Tiny placeholder image (1x1) — frontend uses gradient fallback if missing/tiny
        drone_b64 = None

        frames.append(
            {
                "timestamp": t,
                "estimated_position": {
                    "lat": fused_lat,
                    "lon": fused_lon,
                    "confidence": confidence,
                    "error_radius_m": err_radius,
                    "source": source,
                },
                "ground_truth": {
                    "lat": lat,
                    "lon": lon,
                    "confidence": 1.0,
                    "error_radius_m": 0.0,
                    "source": "truth",
                },
                "top_matches": [
                    {
                        "satellite_patch_path": f"patch_demo_{j}.png",
                        "lat": lat + rng.normal(0, 0.001),
                        "lon": lon + rng.normal(0, 0.001),
                        "similarity_score": max(0.2, confidence - 0.05 * j),
                    }
                    for j in range(3)
                ],
                "imu_only_position": {
                    "lat": imu_lat,
                    "lon": imu_lon,
                    "confidence": 0.2,
                    "error_radius_m": imu_err,
                    "source": "imu",
                },
                "visual_only_position": {
                    "lat": v_lat,
                    "lon": v_lon,
                    "confidence": confidence,
                    "error_radius_m": 80.0,
                    "source": "visual",
                },
                "ekf_state": {
                    "x": [fused_lat, fused_lon, dn / 0.5, de / 0.5, heading],
                    "P": [[1, 0], [0, 1]],
                    "heading": heading,
                    "vn": dn / 0.5,
                    "ve": de / 0.5,
                },
                "metrics": {
                    "error_m": err,
                    "imu_error_m": imu_err,
                    "drift_m": imu_err,
                    "frames": i + 1,
                    "fixes": fixes,
                    "avg_error": float(np.mean(errors)),
                    "max_drift": float(np.max(errors)),
                    "fix_rate": fixes / (i + 1),
                    "runtime": t,
                    "visual_fix": visual_fix,
                },
                "drone_image_b64": drone_b64,
                "altitude_m": 200.0,
                "heading": heading % 360,
                "speed_mps": speed,
                "gps_jammed": True,
                "mode": mode,
            }
        )
    return frames


def main() -> None:
    out = ROOT / "frontend" / "public" / "demo" / "simulation.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    frames = generate_demo_frames(1000)
    out.write_text(json.dumps(frames), encoding="utf-8")
    size_mb = out.stat().st_size / (1024 * 1024)
    print(f"Wrote {len(frames)} frames -> {out} ({size_mb:.2f} MB)")


if __name__ == "__main__":
    main()
