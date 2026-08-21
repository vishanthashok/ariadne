"""Build FAISS index from satellite patch embeddings (pretrained or trained)."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F
from dotenv import load_dotenv
from PIL import Image
from torchvision import models, transforms
from tqdm import tqdm

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")


IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]


def get_transform(image_size: int = 224):
    return transforms.Compose(
        [
            transforms.Resize((image_size, image_size)),
            transforms.ToTensor(),
            transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
        ]
    )


def load_pretrained_encoder(device: torch.device):
    weights = models.ResNet50_Weights.IMAGENET1K_V2
    backbone = models.resnet50(weights=weights)
    backbone.fc = torch.nn.Identity()
    backbone.eval().to(device)
    return backbone


def load_trained_encoder(checkpoint: Path, device: torch.device):
    from model.architectures.feature_extractor import FeatureExtractor
    from model.config import TrainConfig

    cfg = TrainConfig()
    model = FeatureExtractor(embedding_dim=cfg.embedding_dim)
    state = torch.load(checkpoint, map_location=device, weights_only=False)
    if isinstance(state, dict) and "model_state_dict" in state:
        # may be full siamese
        sd = state["model_state_dict"]
        # strip encoder. prefix if present
        filtered = {}
        for k, v in sd.items():
            if k.startswith("encoder."):
                filtered[k[len("encoder.") :]] = v
            elif not k.startswith("encoder"):
                # try direct
                filtered[k] = v
        try:
            model.load_state_dict(filtered, strict=False)
        except Exception:
            model.load_state_dict(sd, strict=False)
    else:
        model.load_state_dict(state, strict=False)
    model.eval().to(device)
    return model


@torch.no_grad()
def embed_image(model, img: Image.Image, transform, device, trained: bool) -> np.ndarray:
    x = transform(img.convert("RGB")).unsqueeze(0).to(device)
    if trained:
        emb = model(x)
    else:
        emb = model(x)
        emb = F.normalize(emb, dim=-1)
    return emb.squeeze(0).cpu().numpy().astype(np.float32)


def build_faiss_index(
    patches_dir: Path | None = None,
    out_dir: Path | None = None,
    checkpoint: Path | None = None,
    index_name: str = "satellite.index",
) -> Path:
    import faiss

    patches_dir = patches_dir or (ROOT / "data" / "processed" / "satellite_patches")
    out_dir = out_dir or (ROOT / "data" / "faiss_index")
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest = patches_dir / "manifest.csv"
    if not manifest.exists():
        raise FileNotFoundError(f"Missing {manifest}")

    with manifest.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    transform = get_transform()
    trained = checkpoint is not None and Path(checkpoint).exists()
    if trained:
        print(f"Using trained encoder: {checkpoint}")
        model = load_trained_encoder(Path(checkpoint), device)
    else:
        print("Using pretrained ResNet-50 ImageNet features")
        model = load_pretrained_encoder(device)

    embeddings = []
    mapping = []
    for row in tqdm(rows, desc="Embedding patches"):
        path = patches_dir / row["filename"]
        if not path.exists():
            continue
        img = Image.open(path)
        emb = embed_image(model, img, transform, device, trained)
        embeddings.append(emb)
        mapping.append(
            {
                "index": len(mapping),
                "filename": row["filename"],
                "lat": float(row["center_lat"]),
                "lon": float(row["center_lon"]),
            }
        )

    if not embeddings:
        raise RuntimeError("No embeddings computed — empty patch set")

    X = np.stack(embeddings, axis=0).astype(np.float32)
    faiss.normalize_L2(X)
    index = faiss.IndexFlatIP(X.shape[1])
    index.add(X)

    index_path = out_dir / index_name
    faiss.write_index(index, str(index_path))
    coords_path = out_dir / "index_to_coords.json"
    if index_name != "satellite.index":
        coords_path = out_dir / f"{Path(index_name).stem}_to_coords.json"
    # Always write primary mapping name expected by API for trained index
    coords_path = out_dir / "index_to_coords.json"
    if "trained" in index_name:
        coords_path = out_dir / "trained_index_to_coords.json"
        # also keep primary updated for API convenience
        (out_dir / "index_to_coords.json").write_text(json.dumps(mapping, indent=2))
    coords_path.write_text(json.dumps(mapping, indent=2))

    size_mb = index_path.stat().st_size / (1024 * 1024)
    # sample query
    import time

    q = X[:1]
    t0 = time.perf_counter()
    index.search(q, 5)
    dt = (time.perf_counter() - t0) * 1000
    print(f"Indexed {len(mapping)} vectors | index size {size_mb:.2f} MB | sample query {dt:.2f} ms")
    print(f"Saved: {index_path}")
    return index_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Build FAISS index from satellite patches")
    parser.add_argument("--checkpoint", type=str, default=None)
    parser.add_argument("--index-name", type=str, default="satellite.index")
    args = parser.parse_args()
    ckpt = Path(args.checkpoint) if args.checkpoint else None
    build_faiss_index(checkpoint=ckpt, index_name=args.index_name)


if __name__ == "__main__":
    main()
