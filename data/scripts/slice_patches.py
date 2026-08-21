"""Slice GeoTIFF/PNG terrain into overlapping geo-referenced patches."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np
from dotenv import load_dotenv
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")

Image.MAX_IMAGE_PIXELS = None


def load_raster(path: Path) -> tuple[np.ndarray, dict]:
    """Return RGB array (H,W,3) and georef dict."""
    if path.suffix.lower() in {".tif", ".tiff"}:
        try:
            import rasterio

            with rasterio.open(path) as src:
                data = src.read()
                if data.shape[0] >= 3:
                    rgb = np.transpose(data[:3], (1, 2, 0))
                else:
                    rgb = np.stack([data[0]] * 3, axis=-1)
                bounds = src.bounds
                meta = {
                    "min_lon": bounds.left,
                    "min_lat": bounds.bottom,
                    "max_lon": bounds.right,
                    "max_lat": bounds.top,
                    "width": src.width,
                    "height": src.height,
                }
                return rgb.astype(np.uint8), meta
        except Exception as e:
            print(f"rasterio read failed ({e}), trying sidecar JSON")

    png = path if path.suffix.lower() == ".png" else path.with_suffix(".png")
    meta_path = path.with_suffix(".json")
    if not meta_path.exists():
        # look for synthetic_terrain.json next to png
        meta_path = png.with_suffix(".json")
    rgb = np.array(Image.open(png).convert("RGB"))
    if meta_path.exists():
        meta = json.loads(meta_path.read_text())
    else:
        meta = {
            "min_lon": 37.5,
            "min_lat": 48.0,
            "max_lon": 38.5,
            "max_lat": 48.8,
            "width": rgb.shape[1],
            "height": rgb.shape[0],
        }
    return rgb, meta


def pixel_to_lonlat(x: float, y: float, meta: dict) -> tuple[float, float]:
    lon = meta["min_lon"] + (x / meta["width"]) * (meta["max_lon"] - meta["min_lon"])
    lat = meta["max_lat"] - (y / meta["height"]) * (meta["max_lat"] - meta["min_lat"])
    return lat, lon


def slice_patches(
    tile_size: int = 256,
    overlap: float = 0.25,
    raw_dir: Path | None = None,
    out_dir: Path | None = None,
) -> Path:
    raw_dir = raw_dir or (ROOT / "data" / "raw")
    out_dir = out_dir or (ROOT / "data" / "processed" / "satellite_patches")
    out_dir.mkdir(parents=True, exist_ok=True)

    sources = list(raw_dir.glob("*.tif")) + list(raw_dir.glob("*.tiff")) + list(raw_dir.glob("*.png"))
    if not sources:
        raise FileNotFoundError(f"No rasters in {raw_dir}. Run download_sentinel first.")

    stride = max(1, int(tile_size * (1 - overlap)))
    rows = []
    total = 0

    for src in sources:
        rgb, meta = load_raster(src)
        h, w = rgb.shape[:2]
        print(f"Slicing {src.name} ({w}x{h}), tile={tile_size}, stride={stride}")
        for y in range(0, h - tile_size + 1, stride):
            for x in range(0, w - tile_size + 1, stride):
                patch = rgb[y : y + tile_size, x : x + tile_size]
                cy, cx = y + tile_size / 2, x + tile_size / 2
                center_lat, center_lon = pixel_to_lonlat(cx, cy, meta)
                min_lat, min_lon = pixel_to_lonlat(x, y + tile_size, meta)
                max_lat, max_lon = pixel_to_lonlat(x + tile_size, y, meta)
                # normalize min/max
                min_lat, max_lat = min(min_lat, max_lat), max(min_lat, max_lat)
                min_lon, max_lon = min(min_lon, max_lon), max(min_lon, max_lon)
                fname = f"patch_{center_lat:.6f}_{center_lon:.6f}.png"
                Image.fromarray(patch).save(out_dir / fname)
                rows.append(
                    {
                        "filename": fname,
                        "center_lat": center_lat,
                        "center_lon": center_lon,
                        "min_lat": min_lat,
                        "min_lon": min_lon,
                        "max_lat": max_lat,
                        "max_lon": max_lon,
                    }
                )
                total += 1

    manifest = out_dir / "manifest.csv"
    with manifest.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "filename",
                "center_lat",
                "center_lon",
                "min_lat",
                "min_lon",
                "max_lat",
                "max_lon",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    res_m = float(__import__("os").getenv("TILE_RESOLUTION_M", "10"))
    print(f"Total patches: {total}")
    print(f"Manifest: {manifest}")
    print(f"Approx resolution: {res_m} m/px | Coverage: {total} patches")
    return manifest


def main() -> None:
    import os

    parser = argparse.ArgumentParser(description="Slice terrain into geo-referenced patches")
    parser.add_argument("--tile-size", type=int, default=int(os.getenv("TILE_SIZE_PX", "256")))
    parser.add_argument("--overlap", type=float, default=0.25)
    args = parser.parse_args()
    slice_patches(tile_size=args.tile_size, overlap=args.overlap)


if __name__ == "__main__":
    main()
