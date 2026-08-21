"""Evaluate trained model and rebuild FAISS index with learned features."""

from __future__ import annotations

import argparse
import csv
import math
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import torch
from PIL import Image
from torchvision import transforms
from tqdm import tqdm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from data.scripts.build_faiss_index import build_faiss_index
from model.architectures.siamese_net import SiameseNet
from model.config import TrainConfig, resolve_device

IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]


def haversine_m(lat1, lon1, lat2, lon2) -> float:
    r = 6_371_000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def load_model(ckpt: Path, device: str) -> SiameseNet:
    cfg = TrainConfig()
    state = torch.load(ckpt, map_location=device, weights_only=False)
    if isinstance(state, dict) and "config" in state:
        cfg.embedding_dim = state["config"].get("embedding_dim", cfg.embedding_dim)
    model = SiameseNet(embedding_dim=cfg.embedding_dim).to(device)
    sd = state["model_state_dict"] if isinstance(state, dict) and "model_state_dict" in state else state
    model.load_state_dict(sd, strict=False)
    model.eval()
    return model


@torch.no_grad()
def evaluate(checkpoint: Path | None = None) -> dict:
    import faiss
    import json

    device = resolve_device("cuda")
    ckpt = checkpoint or (ROOT / "model" / "checkpoints" / "best_model.pt")
    if not ckpt.exists():
        raise FileNotFoundError(f"No checkpoint at {ckpt}. Run train first.")

    print("Rebuilding FAISS index with trained features...")
    build_faiss_index(checkpoint=ckpt, index_name="trained_satellite.index")

    index_path = ROOT / "data" / "faiss_index" / "trained_satellite.index"
    coords_path = ROOT / "data" / "faiss_index" / "trained_index_to_coords.json"
    if not coords_path.exists():
        coords_path = ROOT / "data" / "faiss_index" / "index_to_coords.json"
    index = faiss.read_index(str(index_path))
    mapping = json.loads(coords_path.read_text())

    model = load_model(ckpt, device)
    tf = transforms.Compose(
        [
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
        ]
    )

    pairs_csv = ROOT / "data" / "processed" / "pairs" / "training_pairs.csv"
    processed = ROOT / "data" / "processed"
    with pairs_csv.open(encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if int(float(r.get("label", 1))) == 1]

    # Use last 10% as test
    n = len(rows)
    test_rows = rows[int(n * 0.9) :]
    if len(test_rows) > 200:
        test_rows = test_rows[:: max(1, len(test_rows) // 200)]

    errors = []
    recalls = {t: {"r1": 0, "r5": 0, "n": 0} for t in [500, 1000, 2500, 5000]}
    worst = []

    for row in tqdm(test_rows, desc="Evaluating"):
        true_lat, true_lon = float(row["center_lat"]), float(row["center_lon"])
        img = Image.open(processed / row["drone_view_path"]).convert("RGB")
        x = tf(img).unsqueeze(0).to(device)
        emb = model.encode_drone(x).cpu().numpy().astype(np.float32)
        faiss.normalize_L2(emb)
        scores, idxs = index.search(emb, 10)
        pred_idx = int(idxs[0, 0])
        pred = mapping[pred_idx]
        err = haversine_m(true_lat, true_lon, pred["lat"], pred["lon"])
        errors.append(err)

        for t in recalls:
            recalls[t]["n"] += 1
            # recall@1
            if err <= t:
                recalls[t]["r1"] += 1
            # recall@5
            hit5 = False
            for j in range(min(5, idxs.shape[1])):
                m = mapping[int(idxs[0, j])]
                if haversine_m(true_lat, true_lon, m["lat"], m["lon"]) <= t:
                    hit5 = True
                    break
            if hit5:
                recalls[t]["r5"] += 1

        worst.append((err, row, pred, scores[0, 0]))

    errors_arr = np.array(errors)
    median_err = float(np.median(errors_arr))
    mean_err = float(np.mean(errors_arr))
    print(f"Median localization error: {median_err:.1f} m")
    print(f"Mean localization error: {mean_err:.1f} m")
    for t, v in recalls.items():
        n_ = max(1, v["n"])
        print(f"Recall@1 @ {t}m: {v['r1']/n_:.3f} | Recall@5: {v['r5']/n_:.3f}")

    out_dir = ROOT / "model" / "checkpoints"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Histogram
    plt.figure(figsize=(8, 4))
    plt.hist(errors_arr, bins=40, color="#3b82f6", edgecolor="#1e2130")
    plt.xlabel("Localization error (m)")
    plt.ylabel("Count")
    plt.title("ARIADNE localization error distribution")
    hist_path = out_dir / "error_histogram.png"
    plt.tight_layout()
    plt.savefig(hist_path, dpi=120)
    plt.close()
    print(f"Saved {hist_path}")

    # Worst 10 grid
    worst.sort(key=lambda x: -x[0])
    fig, axes = plt.subplots(10, 3, figsize=(9, 30))
    for i, (err, row, pred, score) in enumerate(worst[:10]):
        drone = Image.open(processed / row["drone_view_path"])
        true_sat = Image.open(processed / row["satellite_patch_path"])
        pred_sat_path = ROOT / "data" / "processed" / "satellite_patches" / pred["filename"]
        pred_sat = Image.open(pred_sat_path) if pred_sat_path.exists() else true_sat
        for ax, im, title in zip(
            axes[i],
            [drone, pred_sat, true_sat],
            [f"drone err={err:.0f}m", f"pred {score:.2f}", "true"],
        ):
            ax.imshow(im)
            ax.set_title(title, fontsize=8)
            ax.axis("off")
    grid_path = out_dir / "confusion_worst10.png"
    plt.tight_layout()
    plt.savefig(grid_path, dpi=100)
    plt.close()
    print(f"Saved {grid_path}")

    return {
        "median_m": median_err,
        "mean_m": mean_err,
        "recalls": recalls,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate ARIADNE model")
    parser.add_argument("--checkpoint", type=str, default=None)
    args = parser.parse_args()
    ckpt = Path(args.checkpoint) if args.checkpoint else None
    evaluate(ckpt)


if __name__ == "__main__":
    main()
