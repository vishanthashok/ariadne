"""Generate synthetic drone camera views and training pairs."""

from __future__ import annotations

import argparse
import csv
import math
import sys
from pathlib import Path

import numpy as np
from dotenv import load_dotenv
from PIL import Image, ImageEnhance, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def augment_drone_view(img: Image.Image, rng: np.random.Generator, aug_id: int) -> tuple[Image.Image, str, float]:
    altitudes = [100, 200, 300, 500]
    altitude = float(altitudes[aug_id % len(altitudes)])
    types = []

    # Rotation
    angle = float(rng.uniform(0, 360))
    out = img.rotate(angle, resample=Image.BICUBIC, expand=False)
    types.append(f"rot{angle:.0f}")

    # Scale jitter (altitude simulation)
    scale = 0.7 + (altitude / 500.0) * 0.3
    crop_frac = float(rng.uniform(0.8, 1.0)) * scale
    crop_frac = min(1.0, max(0.5, crop_frac))
    w, h = out.size
    cw, ch = int(w * crop_frac), int(h * crop_frac)
    left = (w - cw) // 2
    top = (h - ch) // 2
    out = out.crop((left, top, left + cw, top + ch)).resize((w, h), Image.BICUBIC)
    types.append(f"alt{int(altitude)}")

    # Perspective-ish warp via affine shear
    shear = float(rng.uniform(-0.12, 0.12))  # ~15 deg off-nadir proxy
    out = out.transform(
        out.size,
        Image.AFFINE,
        (1, shear, 0, shear * 0.5, 1, 0),
        resample=Image.BICUBIC,
    )
    types.append("persp")

    # Brightness / contrast
    out = ImageEnhance.Brightness(out).enhance(float(rng.uniform(0.7, 1.3)))
    out = ImageEnhance.Contrast(out).enhance(float(rng.uniform(0.7, 1.3)))
    out = ImageEnhance.Color(out).enhance(float(rng.uniform(0.6, 1.4)))
    types.append("color")

    # Blur
    sigma = float(rng.uniform(0.5, 2.0))
    out = out.filter(ImageFilter.GaussianBlur(radius=sigma))
    types.append(f"blur{sigma:.1f}")

    # Noise
    arr = np.array(out).astype(np.float32)
    noise = rng.normal(0, 8, arr.shape)
    if rng.random() < 0.3:
        # salt and pepper
        mask = rng.random(arr.shape[:2])
        arr[mask < 0.01] = 0
        arr[mask > 0.99] = 255
    arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
    out = Image.fromarray(arr)
    types.append("noise")

    return out, "+".join(types), altitude


def generate_drone_views(
    n_views: int = 5,
    patches_dir: Path | None = None,
    drone_dir: Path | None = None,
    pairs_dir: Path | None = None,
    seed: int = 42,
) -> Path:
    patches_dir = patches_dir or (ROOT / "data" / "processed" / "satellite_patches")
    drone_dir = drone_dir or (ROOT / "data" / "processed" / "drone_views")
    pairs_dir = pairs_dir or (ROOT / "data" / "processed" / "pairs")
    drone_dir.mkdir(parents=True, exist_ok=True)
    pairs_dir.mkdir(parents=True, exist_ok=True)

    manifest = patches_dir / "manifest.csv"
    if not manifest.exists():
        raise FileNotFoundError(f"Missing {manifest}. Run slice_patches first.")

    with manifest.open(encoding="utf-8") as f:
        patches = list(csv.DictReader(f))

    rng = np.random.default_rng(seed)
    pairs = []
    pos = 0
    neg = 0

    coords = [(float(p["center_lat"]), float(p["center_lon"]), p["filename"]) for p in patches]

    for p in patches:
        sat_path = patches_dir / p["filename"]
        if not sat_path.exists():
            continue
        img = Image.open(sat_path).convert("RGB")
        lat, lon = float(p["center_lat"]), float(p["center_lon"])
        for i in range(n_views):
            drone_img, aug_type, altitude = augment_drone_view(img, rng, i)
            dname = f"drone_{lat:.6f}_{lon:.6f}_{i}.png"
            drone_img.save(drone_dir / dname)
            pairs.append(
                {
                    "drone_view_path": f"drone_views/{dname}",
                    "satellite_patch_path": f"satellite_patches/{p['filename']}",
                    "center_lat": lat,
                    "center_lon": lon,
                    "altitude_m": altitude,
                    "augmentation_type": aug_type,
                    "label": 1,
                }
            )
            pos += 1

            # Hard negatives: nearby but wrong (2–10 km)
            candidates = []
            for plat, plon, pfn in coords:
                d = haversine_km(lat, lon, plat, plon)
                if 2.0 <= d <= 10.0:
                    candidates.append((pfn, plat, plon, d))
            if not candidates:
                # fallback: any other patch
                candidates = [
                    (pfn, plat, plon, haversine_km(lat, lon, plat, plon))
                    for plat, plon, pfn in coords
                    if pfn != p["filename"]
                ]
            if candidates:
                pick = rng.choice(len(candidates), size=min(5, len(candidates)), replace=False)
                for idx in np.atleast_1d(pick):
                    pfn, plat, plon, _ = candidates[int(idx)]
                    pairs.append(
                        {
                            "drone_view_path": f"drone_views/{dname}",
                            "satellite_patch_path": f"satellite_patches/{pfn}",
                            "center_lat": plat,
                            "center_lon": plon,
                            "altitude_m": altitude,
                            "augmentation_type": "hard_negative",
                            "label": 0,
                        }
                    )
                    neg += 1

    out_csv = pairs_dir / "training_pairs.csv"
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "drone_view_path",
                "satellite_patch_path",
                "center_lat",
                "center_lon",
                "altitude_m",
                "augmentation_type",
                "label",
            ],
        )
        writer.writeheader()
        writer.writerows(pairs)

    ratio = (pos / neg) if neg else float("inf")
    print(f"Total pairs: {len(pairs)} (positives={pos}, negatives={neg}, ratio={ratio:.3f})")
    print(f"Saved: {out_csv}")
    return out_csv


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic drone views and training pairs")
    parser.add_argument("--n-views", type=int, default=5)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    generate_drone_views(n_views=args.n_views, seed=args.seed)


if __name__ == "__main__":
    main()
