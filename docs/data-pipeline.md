# Data Pipeline

## Scripts

| Script | Role |
|--------|------|
| `data/scripts/download_sentinel.py` | Sentinel Hub / STAC if credentials exist; otherwise synthetic Perlin GeoTIFF/PNG |
| `data/scripts/slice_patches.py` | Overlapping 256px patches + `manifest.csv` |
| `data/scripts/generate_drone_views.py` | Augmented drone views + positive/negative `training_pairs.csv` |
| `data/scripts/build_faiss_index.py` | ResNet-50 (pretrained or trained) embeddings → FAISS `IndexFlatIP` |
| `data/scripts/generate_imu_data.py` | 10 synthetic flights with accel/gyro noise models |

## Make targets

```bash
make download-data   # terrain into data/raw/
make process-data    # patches, pairs, FAISS, IMU
```

## Region

Default bbox `37.5,48.0,38.5,48.8` (Donetsk Oblast), configurable via `REGION_BBOX` in `.env`.
