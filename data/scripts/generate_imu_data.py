"""Generate synthetic IMU flight data with realistic noise models."""

from __future__ import annotations

import argparse
import csv
import math
import sys
from pathlib import Path

import numpy as np
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")


def parse_bbox(bbox_str: str) -> tuple[float, float, float, float]:
    parts = [float(x.strip()) for x in bbox_str.split(",")]
    return parts[0], parts[1], parts[2], parts[3]


def meters_to_latlon(lat: float, lon: float, dn: float, de: float) -> tuple[float, float]:
    dlat = dn / 111_320.0
    dlon = de / (111_320.0 * math.cos(math.radians(lat)))
    return lat + dlat, lon + dlon


def generate_flight(
    flight_id: int,
    bbox: tuple[float, float, float, float],
    duration_s: float = 600.0,
    rate_hz: float = 10.0,
    seed: int = 0,
) -> list[dict]:
    rng = np.random.default_rng(seed + flight_id)
    min_lon, min_lat, max_lon, max_lat = bbox
    # Start near center with path variation
    lat = min_lat + (max_lat - min_lat) * float(rng.uniform(0.3, 0.7))
    lon = min_lon + (max_lon - min_lon) * float(rng.uniform(0.3, 0.7))
    alt = float(rng.choice([100, 200, 300, 500]))
    heading = float(rng.uniform(0, 360))
    speed = float(rng.uniform(8, 18))  # m/s

    n = int(duration_s * rate_hz)
    dt = 1.0 / rate_hz

    # Noise params from spec
    accel_bias = rng.normal(0, 0.04 * 9.81e-3, size=3)  # ~0.04 mg
    gyro_bias = rng.normal(0, math.radians(1) / 3600, size=3)  # 1 deg/hr
    accel_rw = 0.07 / math.sqrt(3600)  # m/s/sqrt(hr) -> per sqrt(s)
    gyro_arw = math.radians(0.15) / math.sqrt(3600)

    rows = []
    # Dead-reckon without correction to report max drift
    drift_lat, drift_lon = lat, lon
    max_drift = 0.0

    for i in range(n):
        t = i * dt
        # Gentle path curvature
        heading += float(rng.normal(0, 0.5))
        heading %= 360
        vn = speed * math.cos(math.radians(heading))
        ve = speed * math.sin(math.radians(heading))
        lat, lon = meters_to_latlon(lat, lon, vn * dt, ve * dt)
        # Keep inside bbox with soft bounce
        if lat < min_lat or lat > max_lat:
            heading = (180 - heading) % 360
            lat = float(np.clip(lat, min_lat, max_lat))
        if lon < min_lon or lon > max_lon:
            heading = (-heading) % 360
            lon = float(np.clip(lon, min_lon, max_lon))

        # True specific force approx (level flight)
        ax_t, ay_t, az_t = 0.0, 0.0, 9.81
        gx_t, gy_t, gz_t = 0.0, 0.0, math.radians(float(rng.normal(0, 0.5)))

        ax = ax_t + accel_bias[0] + rng.normal(0, accel_rw)
        ay = ay_t + accel_bias[1] + rng.normal(0, accel_rw)
        az = az_t + accel_bias[2] + rng.normal(0, accel_rw)
        gx = gx_t + gyro_bias[0] + rng.normal(0, gyro_arw)
        gy = gy_t + gyro_bias[1] + rng.normal(0, gyro_arw)
        gz = gz_t + gyro_bias[2] + rng.normal(0, gyro_arw)

        # Uncorrected IMU dead reckoning drift estimate
        drift_heading = heading + math.degrees(gyro_bias[2] * t)
        dvn = speed * math.cos(math.radians(drift_heading)) * dt
        dve = speed * math.sin(math.radians(drift_heading)) * dt
        # add accel bias integration roughly
        dvn += accel_bias[0] * t * dt * 0.01
        dve += accel_bias[1] * t * dt * 0.01
        drift_lat, drift_lon = meters_to_latlon(drift_lat, drift_lon, dvn, dve)
        dlat_m = (drift_lat - lat) * 111_320
        dlon_m = (drift_lon - lon) * 111_320 * math.cos(math.radians(lat))
        drift_m = math.hypot(dlat_m, dlon_m)
        max_drift = max(max_drift, drift_m)

        rows.append(
            {
                "timestamp": round(t, 3),
                "ax": ax,
                "ay": ay,
                "az": az,
                "gx": gx,
                "gy": gy,
                "gz": gz,
                "true_lat": lat,
                "true_lon": lon,
                "true_alt": alt,
                "true_heading": heading,
                "true_speed": speed,
            }
        )

    return rows, max_drift


def generate_imu_data(
    n_flights: int = 10,
    out_dir: Path | None = None,
    duration_s: float = 300.0,
) -> Path:
    import os

    out_dir = out_dir or (ROOT / "data" / "processed" / "imu_data")
    out_dir.mkdir(parents=True, exist_ok=True)
    bbox = parse_bbox(os.getenv("REGION_BBOX", "37.5,48.0,38.5,48.8"))

    total_hours = 0.0
    for fid in range(n_flights):
        rows, max_drift = generate_flight(fid, bbox, duration_s=duration_s)
        path = out_dir / f"flight_{fid}.csv"
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "timestamp",
                    "ax",
                    "ay",
                    "az",
                    "gx",
                    "gy",
                    "gz",
                    "true_lat",
                    "true_lon",
                    "true_alt",
                    "true_heading",
                    "true_speed",
                ],
            )
            writer.writeheader()
            writer.writerows(rows)
        hours = duration_s / 3600.0
        total_hours += hours
        print(f"flight_{fid}: {len(rows)} samples | max uncorrected drift ~{max_drift:.1f} m")

    print(f"Total flight hours simulated: {total_hours:.2f}")
    return out_dir


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic IMU flight CSVs")
    parser.add_argument("--n-flights", type=int, default=10)
    parser.add_argument("--duration", type=float, default=300.0)
    args = parser.parse_args()
    generate_imu_data(n_flights=args.n_flights, duration_s=args.duration)


if __name__ == "__main__":
    main()
