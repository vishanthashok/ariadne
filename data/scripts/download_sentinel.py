"""Download Sentinel-2 imagery or generate synthetic Perlin terrain GeoTIFF."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import numpy as np
from dotenv import load_dotenv
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

load_dotenv(ROOT / ".env")


def parse_bbox(bbox_str: str) -> tuple[float, float, float, float]:
    parts = [float(x.strip()) for x in bbox_str.split(",")]
    if len(parts) != 4:
        raise ValueError("REGION_BBOX must be min_lon,min_lat,max_lon,max_lat")
    return parts[0], parts[1], parts[2], parts[3]


def generate_perlin_terrain(size: int = 5000, seed: int = 42) -> np.ndarray:
    """Generate RGB terrain-like image via layered value noise (no GDAL required)."""
    rng = np.random.default_rng(seed)

    def value_noise(h: int, w: int, scale: int) -> np.ndarray:
        gh, gw = max(2, h // scale + 1), max(2, w // scale + 1)
        grid = rng.random((gh, gw))
        ys = np.linspace(0, gh - 1, h)
        xs = np.linspace(0, gw - 1, w)
        yi = np.floor(ys).astype(int)
        xi = np.floor(xs).astype(int)
        yf = ys - yi
        xf = xs - xi
        yi1 = np.clip(yi + 1, 0, gh - 1)
        xi1 = np.clip(xi + 1, 0, gw - 1)
        # bilinear
        n00 = grid[yi][:, xi]
        n10 = grid[yi][:, xi1]
        n01 = grid[yi1][:, xi]
        n11 = grid[yi1][:, xi1]
        top = n00 * (1 - xf) + n10 * xf
        bot = n01 * (1 - xf) + n11 * xf
        return (top.T * (1 - yf) + bot.T * yf).T

    elev = (
        0.5 * value_noise(size, size, 128)
        + 0.3 * value_noise(size, size, 64)
        + 0.15 * value_noise(size, size, 32)
        + 0.05 * value_noise(size, size, 16)
    )
    elev = (elev - elev.min()) / (elev.max() - elev.min() + 1e-8)

    # Terrain color map: water / field / soil / urban-ish
    r = np.zeros_like(elev)
    g = np.zeros_like(elev)
    b = np.zeros_like(elev)

    water = elev < 0.28
    field = (elev >= 0.28) & (elev < 0.55)
    soil = (elev >= 0.55) & (elev < 0.75)
    urban = elev >= 0.75

    r[water], g[water], b[water] = 0.15, 0.35, 0.55
    r[field], g[field], b[field] = 0.35, 0.55, 0.25
    r[soil], g[soil], b[soil] = 0.55, 0.45, 0.30
    r[urban], g[urban], b[urban] = 0.45, 0.45, 0.48

    # Add texture
    tex = value_noise(size, size, 8) * 0.08
    rgb = np.stack([r, g, b], axis=-1)
    rgb = np.clip(rgb + tex[..., None], 0, 1)
    return (rgb * 255).astype(np.uint8)


def save_geotiff_or_png(
    rgb: np.ndarray,
    out_path: Path,
    bbox: tuple[float, float, float, float],
) -> Path:
    """Try rasterio GeoTIFF; fall back to PNG + worldfile sidecar."""
    min_lon, min_lat, max_lon, max_lat = bbox
    h, w = rgb.shape[:2]
    try:
        import rasterio
        from rasterio.transform import from_bounds

        transform = from_bounds(min_lon, min_lat, max_lon, max_lat, w, h)
        out_tif = out_path.with_suffix(".tif")
        with rasterio.open(
            out_tif,
            "w",
            driver="GTiff",
            height=h,
            width=w,
            count=3,
            dtype="uint8",
            crs="EPSG:4326",
            transform=transform,
            compress="lzw",
        ) as dst:
            for i in range(3):
                dst.write(rgb[:, :, i], i + 1)
        print(f"Saved GeoTIFF: {out_tif}")
        return out_tif
    except Exception as e:
        print(f"rasterio unavailable ({e}); saving PNG + metadata JSON")
        out_png = out_path.with_suffix(".png")
        Image.fromarray(rgb).save(out_png)
        meta = out_path.with_suffix(".json")
        import json

        meta.write_text(
            json.dumps(
                {
                    "min_lon": min_lon,
                    "min_lat": min_lat,
                    "max_lon": max_lon,
                    "max_lat": max_lat,
                    "width": w,
                    "height": h,
                    "crs": "EPSG:4326",
                },
                indent=2,
            )
        )
        print(f"Saved PNG: {out_png}")
        return out_png


def try_sentinel_download(bbox: tuple[float, float, float, float], out_dir: Path) -> Path | None:
    client_id = os.getenv("SENTINEL_HUB_CLIENT_ID", "").strip()
    client_secret = os.getenv("SENTINEL_HUB_CLIENT_SECRET", "").strip()
    if not client_id or not client_secret:
        print("No Sentinel Hub credentials — using synthetic terrain fallback.")
        return None
    try:
        import httpx

        # Minimal auth probe; full STAC download is environment-specific
        print("Sentinel credentials present; attempting STAC search...")
        # Fall through to synthetic if network/API fails
        with httpx.Client(timeout=15.0) as client:
            r = client.get("https://catalogue.dataspace.copernicus.eu/stac")
            if r.status_code >= 400:
                print(f"STAC catalogue unavailable ({r.status_code}); using fallback.")
                return None
        print("STAC reachable but automated L2A download requires extra setup; using synthetic fallback.")
        return None
    except Exception as e:
        print(f"Sentinel download failed ({e}); using synthetic fallback.")
        return None


def download_or_generate(
    out_dir: Path | None = None,
    bbox: tuple[float, float, float, float] | None = None,
    size: int = 5000,
) -> Path:
    out_dir = out_dir or (ROOT / "data" / "raw")
    out_dir.mkdir(parents=True, exist_ok=True)
    if bbox is None:
        bbox = parse_bbox(os.getenv("REGION_BBOX", "37.5,48.0,38.5,48.8"))

    existing = try_sentinel_download(bbox, out_dir)
    if existing is not None:
        return existing

    print(f"Generating {size}x{size} synthetic Perlin terrain for bbox {bbox}...")
    rgb = generate_perlin_terrain(size=size)
    area_km2 = abs(bbox[2] - bbox[0]) * 111 * abs(bbox[3] - bbox[1]) * 111 * np.cos(np.radians((bbox[1] + bbox[3]) / 2))
    print(f"Scenes found: 0 (synthetic) | Area covered: ~{area_km2:.0f} km²")
    return save_geotiff_or_png(rgb, out_dir / "synthetic_terrain", bbox)


def main() -> None:
    parser = argparse.ArgumentParser(description="Download Sentinel-2 or generate synthetic terrain")
    parser.add_argument("--size", type=int, default=2000, help="Synthetic image size (default 2000 for speed)")
    parser.add_argument("--out", type=str, default=None)
    args = parser.parse_args()
    out = Path(args.out) if args.out else None
    path = download_or_generate(out_dir=out, size=args.size)
    print(f"Done: {path}")


if __name__ == "__main__":
    main()
