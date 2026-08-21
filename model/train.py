"""Train Siamese geo-localization model."""

from __future__ import annotations

import argparse
import csv
import sys
import time
from pathlib import Path

import torch
import torch.nn.functional as F
from PIL import Image
from torch.utils.data import DataLoader, Dataset, Subset
from torchvision import transforms
from tqdm import tqdm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from model.architectures.siamese_net import SiameseNet
from model.config import TrainConfig, resolve_device
from model.losses.contrastive import InfoNCELoss, TripletLoss

IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]


class PairDataset(Dataset):
    def __init__(self, rows: list[dict], processed_root: Path, image_size: int, train: bool):
        self.rows = rows
        self.root = processed_root
        aug = []
        if train:
            aug = [
                transforms.RandomHorizontalFlip(),
                transforms.ColorJitter(0.2, 0.2, 0.2, 0.1),
                transforms.RandomGrayscale(p=0.1),
            ]
        self.tf = transforms.Compose(
            [
                transforms.Resize((image_size, image_size)),
                *aug,
                transforms.ToTensor(),
                transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
            ]
        )

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, idx: int):
        row = self.rows[idx]
        drone = Image.open(self.root / row["drone_view_path"]).convert("RGB")
        sat = Image.open(self.root / row["satellite_patch_path"]).convert("RGB")
        return self.tf(drone), self.tf(sat), float(row.get("label", 1))


def load_positive_pairs(pairs_csv: Path) -> list[dict]:
    with pairs_csv.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return [r for r in rows if int(float(r.get("label", 1))) == 1]


@torch.no_grad()
def retrieval_accuracy(model: SiameseNet, loader: DataLoader, device: str, topk=(1, 5)) -> dict:
    model.eval()
    drone_embs, sat_embs = [], []
    for drone, sat, _ in loader:
        d, s = model(drone.to(device), sat.to(device))
        drone_embs.append(d)
        sat_embs.append(s)
    if not drone_embs:
        return {f"recall@{k}": 0.0 for k in topk}
    D = torch.cat(drone_embs, dim=0)
    S = torch.cat(sat_embs, dim=0)
    sim = D @ S.T
    ranks = sim.argsort(dim=1, descending=True)
    labels = torch.arange(sim.size(0), device=sim.device)
    out = {}
    for k in topk:
        correct = (ranks[:, :k] == labels.unsqueeze(1)).any(dim=1).float().mean().item()
        out[f"recall@{k}"] = correct
    return out


def train(cfg: TrainConfig) -> Path:
    device = resolve_device(cfg.device)
    cfg.device = device
    print(f"Device: {device}")

    pairs_csv = ROOT / "data" / "processed" / "pairs" / "training_pairs.csv"
    processed = ROOT / "data" / "processed"
    if not pairs_csv.exists():
        raise FileNotFoundError(f"Missing {pairs_csv}. Run process-data first.")

    positives = load_positive_pairs(pairs_csv)
    if len(positives) < 10:
        raise RuntimeError(f"Too few positive pairs: {len(positives)}")

    n = len(positives)
    n_train = int(n * cfg.train_split)
    n_val = int(n * cfg.val_split)
    indices = list(range(n))
    # deterministic split
    g = torch.Generator().manual_seed(42)
    perm = torch.randperm(n, generator=g).tolist()
    train_idx = perm[:n_train]
    val_idx = perm[n_train : n_train + n_val]
    test_idx = perm[n_train + n_val :]

    full = PairDataset(positives, processed, cfg.image_size, train=True)
    val_ds = PairDataset(positives, processed, cfg.image_size, train=False)
    train_loader = DataLoader(
        Subset(full, train_idx),
        batch_size=cfg.batch_size,
        shuffle=True,
        num_workers=0,
        drop_last=True,
    )
    val_loader = DataLoader(
        Subset(val_ds, val_idx if val_idx else train_idx[: max(1, len(train_idx) // 10)]),
        batch_size=cfg.batch_size,
        shuffle=False,
        num_workers=0,
    )

    # Rough time estimate
    steps = max(1, len(train_loader)) * cfg.num_epochs
    sec_per_step = 0.8 if device == "cpu" else 0.05
    print(f"Estimated training time: ~{steps * sec_per_step / 60:.1f} min ({len(positives)} positives)")

    model = SiameseNet(embedding_dim=cfg.embedding_dim).to(device)
    if cfg.loss_type == "triplet":
        criterion = TripletLoss(margin=cfg.margin)
    else:
        criterion = InfoNCELoss(temperature=cfg.temperature)
    opt = torch.optim.AdamW(model.parameters(), lr=cfg.learning_rate, weight_decay=cfg.weight_decay)

    ckpt_dir = ROOT / cfg.checkpoint_dir
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    best_path = ckpt_dir / "best_model.pt"
    best_recall = -1.0
    patience = 10
    stale = 0
    t0 = time.time()

    for epoch in range(1, cfg.num_epochs + 1):
        model.train()
        losses = []
        top1_batch = []
        for drone, sat, _ in tqdm(train_loader, desc=f"Epoch {epoch}/{cfg.num_epochs}"):
            drone, sat = drone.to(device), sat.to(device)
            d_emb, s_emb = model(drone, sat)
            if cfg.loss_type == "triplet":
                # use in-batch negatives: shift positives
                neg = torch.roll(s_emb, shifts=1, dims=0)
                loss = criterion(d_emb, s_emb, neg)
            else:
                loss = criterion(d_emb, s_emb)
            opt.zero_grad()
            loss.backward()
            opt.step()
            losses.append(loss.item())
            with torch.no_grad():
                sim = d_emb @ s_emb.T
                pred = sim.argmax(dim=1)
                labels = torch.arange(sim.size(0), device=device)
                top1_batch.append((pred == labels).float().mean().item())

        val_metrics = retrieval_accuracy(model, val_loader, device)
        train_loss = sum(losses) / max(1, len(losses))
        train_top1 = sum(top1_batch) / max(1, len(top1_batch))
        print(
            f"Epoch {epoch}: loss={train_loss:.4f} train@1={train_top1:.3f} "
            f"val@1={val_metrics['recall@1']:.3f} val@5={val_metrics['recall@5']:.3f}"
        )

        if val_metrics["recall@1"] > best_recall:
            best_recall = val_metrics["recall@1"]
            stale = 0
            torch.save(
                {
                    "model_state_dict": model.state_dict(),
                    "config": cfg.to_dict(),
                    "val_recall@1": best_recall,
                },
                best_path,
            )
            print(f"  saved checkpoint -> {best_path}")
        else:
            stale += 1
            if stale >= patience:
                print("Early stopping.")
                break

    elapsed = time.time() - t0
    print(
        f"Training done in {elapsed/60:.1f} min | best val recall@1={best_recall:.3f} | checkpoint={best_path}"
    )
    # keep test indices for evaluate
    (ckpt_dir / "test_indices.txt").write_text("\n".join(map(str, test_idx)))
    return best_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Train ARIADNE Siamese geo-localizer")
    parser.add_argument("--epochs", type=int, default=None)
    parser.add_argument("--batch-size", type=int, default=None)
    parser.add_argument("--lr", type=float, default=None)
    parser.add_argument("--device", type=str, default=None)
    args = parser.parse_args()
    cfg = TrainConfig()
    if args.epochs is not None:
        cfg.num_epochs = args.epochs
    if args.batch_size is not None:
        cfg.batch_size = args.batch_size
    if args.lr is not None:
        cfg.learning_rate = args.lr
    if args.device is not None:
        cfg.device = args.device
    train(cfg)


if __name__ == "__main__":
    main()
