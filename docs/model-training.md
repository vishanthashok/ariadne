# Model Training

## Architecture

- Backbone: ResNet-50 (ImageNet), early layers frozen
- Projection: `2048 → 512 → embedding_dim` with BatchNorm + ReLU + L2 normalize
- Siamese shared weights for drone and satellite branches
- Loss: InfoNCE (default) or triplet

## Train

```bash
make train
# or full GPU run:
python -m model.train --epochs 50 --batch-size 64
```

Checkpoints land in `model/checkpoints/best_model.pt` (best val recall@1).

## Evaluate

```bash
make evaluate
```

Rebuilds `trained_satellite.index`, reports median/mean error, recall@1/5 at distance thresholds, and writes histogram / confusion PNGs.

## Inference

`model/inference.py` → embed drone frame → FAISS top-5 → confidence = distinctiveness → EKF update if confidence > 0.3.
