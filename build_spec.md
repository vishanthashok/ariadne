# ARIADNE — GPS-Denied Visual-Inertial Navigation for Autonomous Drone Systems

## PROJECT IDENTITY

- Repo name: `ariadne`
- Tagline: "GPS-denied visual-inertial navigation for autonomous drone systems"
- Named after Ariadne from Greek mythology, who gave Theseus a thread to navigate the Minotaur's labyrinth when no map existed. This system gives a drone a "thread" (visual terrain matching) to navigate when GPS is jammed.
- Inspired by Ukraine's Ministry of Defence publicly documented challenges with GPS jamming and spoofing in contested airspace (2024-2026).

---

## WHAT THIS SYSTEM DOES (end to end)

A drone flies over terrain. GPS is jammed. The drone's onboard camera captures downward-facing images of the ground below. ARIADNE takes those images, matches them against a pre-loaded satellite reference map, and outputs an estimated latitude/longitude. It fuses that visual estimate with inertial measurement unit (IMU) data using an Extended Kalman Filter to smooth the position estimate and handle moments when the visual match is uncertain.

The UI shows all of this happening in real time: drone camera feed, satellite reference tiles, estimated position on a map, error metrics, and drift visualization.

---

## TECH STACK (exact versions)

### Backend / ML
- Python 3.11+
- PyTorch 2.2+ (model training and inference)
- torchvision (pretrained ResNet-50 backbone)
- FAISS (facebook/faiss-cpu or faiss-gpu, vector similarity search)
- rasterio 1.3+ (geospatial raster I/O)
- GDAL (via rasterio, coordinate transforms)
- Pillow (image processing)
- NumPy, SciPy (IMU simulation, signal processing)
- filterpy (Extended Kalman Filter implementation)
- FastAPI 0.110+ (inference API server)
- uvicorn (ASGI server)
- websockets (real-time streaming to frontend)
- httpx or requests (Sentinel-2 API calls)
- shapely (geospatial bounding box math)
- pyproj (coordinate system conversions)

### Frontend
- Next.js 14 (App Router, TypeScript)
- React 18
- Mapbox GL JS v3 (satellite base map, trajectory overlay)
- deck.gl (trajectory visualization, confidence heatmap)
- Recharts (telemetry line charts)
- Framer Motion (panel transitions, pulse animations)
- Tailwind CSS 3.4
- shadcn/ui (component primitives: sliders, toggles, cards)
- Lucide React (icon set)
- Socket.io client (WebSocket connection to FastAPI)

### Infrastructure
- Docker + docker-compose (full stack containerization)
- Makefile (single-command build/train/run)

---

## REPO STRUCTURE (create this exact tree)

```
ariadne/
├── README.md
├── Makefile
├── docker-compose.yml
├── .env.example
├── .gitignore
├── docs/
│   ├── architecture.md
│   ├── data-pipeline.md
│   └── model-training.md
├── data/
│   ├── raw/                    # downloaded Sentinel-2 tiles (gitignored)
│   ├── processed/
│   │   ├── satellite_patches/  # sliced geo-referenced patches
│   │   ├── drone_views/        # synthetic drone camera views
│   │   └── pairs/              # training pairs CSV
│   ├── faiss_index/            # FAISS index files
│   └── scripts/
│       ├── download_sentinel.py
│       ├── slice_patches.py
│       ├── generate_drone_views.py
│       ├── build_faiss_index.py
│       └── generate_imu_data.py
├── model/
│   ├── architectures/
│   │   ├── siamese_net.py
│   │   └── feature_extractor.py
│   ├── losses/
│   │   └── contrastive.py
│   ├── train.py
│   ├── evaluate.py
│   ├── ekf.py
│   ├── inference.py
│   └── config.py
├── api/
│   ├── main.py
│   ├── schemas.py
│   ├── ws_manager.py
│   └── simulation.py
├── frontend/
│   ├── package.json
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   ├── next.config.js
│   ├── public/
│   │   └── demo/               # pre-recorded demo data JSON
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx
│   │   │   └── globals.css
│   │   ├── components/
│   │   │   ├── DroneViewPanel.tsx
│   │   │   ├── MapPanel.tsx
│   │   │   ├── TelemetryPanel.tsx
│   │   │   ├── ControlBar.tsx
│   │   │   ├── ConfidenceRing.tsx
│   │   │   ├── MatchCard.tsx
│   │   │   └── MetricChart.tsx
│   │   ├── hooks/
│   │   │   ├── useSimulation.ts
│   │   │   └── useWebSocket.ts
│   │   ├── lib/
│   │   │   ├── mapbox.ts
│   │   │   ├── types.ts
│   │   │   └── constants.ts
│   │   └── styles/
│   │       └── theme.ts
│   └── .env.local.example
└── notebooks/
    └── walkthrough.ipynb
```

---

## COLOR PALETTE AND DESIGN TOKENS

Use these exact values everywhere. Do not deviate.

```
Background:        #06060a (near-black with blue undertone)
Surface:           #0f1117 (card/panel backgrounds)
Surface elevated:  #161922 (hover states, active panels)
Border:            #1e2130 (subtle panel dividers)
Text primary:      #e4e4e7 (zinc-200)
Text secondary:    #71717a (zinc-500)
Text muted:        #3f3f46 (zinc-700)

Estimated path:    #3b82f6 (blue-500, the ARIADNE thread)
Ground truth path: #f59e0b (amber-500)
Error/jamming:     #ef4444 (red-500)
High confidence:   #22c55e (green-500)
Low confidence:    #f97316 (orange-500)
Accent glow:       #60a5fa (blue-400, used for pulse effects)

Font:              Inter (sans-serif)
Monospace:         JetBrains Mono (telemetry readouts)
```

---

## BUILD PHASES

Execute these phases in exact order. Complete each phase fully before moving to the next. Test each phase before proceeding.

---

### PHASE 0: PROJECT SCAFFOLD

Create the full directory tree shown above. Initialize:

1. Root `pyproject.toml` or `requirements.txt` with all Python dependencies listed above.
2. `frontend/package.json` with all JS dependencies listed above.
3. `.gitignore` that excludes: `data/raw/`, `data/processed/`, `data/faiss_index/`, `__pycache__/`, `.env`, `node_modules/`, `.next/`, `*.pt`, `*.pth`, `*.onnx`, `*.faiss`.
4. `.env.example` with placeholders for: `SENTINEL_HUB_CLIENT_ID`, `SENTINEL_HUB_CLIENT_SECRET`, `MAPBOX_ACCESS_TOKEN`, `REGION_BBOX` (default: `37.5,48.0,38.5,48.8` which is a 100km x 90km area in Donetsk Oblast), `TILE_SIZE_PX` (default: 256), `TILE_RESOLUTION_M` (default: 10).
5. `Makefile` with targets: `setup`, `download-data`, `process-data`, `train`, `evaluate`, `serve-api`, `serve-frontend`, `demo`, `docker-up`.
6. `docker-compose.yml` with three services: `api` (Python FastAPI on port 8000), `frontend` (Next.js on port 3000), `training` (GPU-enabled Python container, only used for training).

Deliverable: Running `make setup` installs all dependencies. The directory tree exists and is clean.

---

### PHASE 1: DATA PIPELINE

Build five scripts in `data/scripts/`. Each script must be runnable standalone and also callable as a module.

#### 1A: `download_sentinel.py`

Purpose: Download Sentinel-2 L2A satellite imagery for the configured region.

Implementation:
- Read `REGION_BBOX` from `.env` (format: `min_lon,min_lat,max_lon,max_lat`).
- Use the Copernicus Open Access Hub STAC API (https://dataspace.copernicus.eu/) or SentinelHub API to search for cloud-free (<15% cloud cover) Sentinel-2 L2A scenes covering the bounding box.
- Download the true-color (B04, B03, B02) bands at 10m resolution.
- Save as GeoTIFF files in `data/raw/`.
- If the user doesn't have Sentinel credentials, provide a FALLBACK mode that downloads from the free Copernicus Browser export or uses a bundled sample GeoTIFF (include a script that generates a 5000x5000 pixel synthetic terrain image using Perlin noise with realistic color mapping as a zero-dependency fallback).
- Print progress: number of scenes found, download progress, total area covered.

#### 1B: `slice_patches.py`

Purpose: Slice the large GeoTIFF into a grid of overlapping geo-referenced patches.

Implementation:
- Read each GeoTIFF in `data/raw/`.
- Slice into `TILE_SIZE_PX x TILE_SIZE_PX` patches (default 256x256) with 25% overlap.
- For each patch, compute and store: center latitude, center longitude, bounding box, and the image as a PNG.
- Save patches to `data/processed/satellite_patches/` with filename format: `patch_{lat}_{lon}.png`.
- Save a manifest CSV: `data/processed/satellite_patches/manifest.csv` with columns: `filename, center_lat, center_lon, min_lat, min_lon, max_lat, max_lon`.
- Print: total patches created, area coverage, resolution.

#### 1C: `generate_drone_views.py`

Purpose: Generate synthetic drone-camera images for known positions to create training pairs.

Implementation:
- For each satellite patch in the manifest:
  - Generate N=5 synthetic drone views by applying random augmentations that simulate what a downward-facing drone camera would see:
    - Random rotation (0-360 degrees)
    - Slight perspective warp (simulating non-nadir viewing angles up to 15 degrees off-vertical)
    - Scale jitter (simulating altitude variation: 100m, 200m, 300m, 500m)
    - Brightness/contrast jitter (simulating different times of day)
    - Gaussian blur (sigma 0.5-2.0, simulating motion blur and atmospheric haze)
    - Random crop (80-100% of tile, simulating partial FOV)
    - Color jitter (simulating seasonal vegetation changes)
    - Optional: add synthetic noise (Gaussian, salt-and-pepper) to simulate low-quality cameras
- Save drone views to `data/processed/drone_views/` with filename: `drone_{lat}_{lon}_{augmentation_id}.png`.
- Save a pairs CSV: `data/processed/pairs/training_pairs.csv` with columns: `drone_view_path, satellite_patch_path, center_lat, center_lon, altitude_m, augmentation_type`.
- Include hard negatives: for each drone view, also record 5 nearby-but-wrong satellite patches (within 2-10km) as negative pairs.
- Print: total pairs created, positive/negative ratio.

#### 1D: `build_faiss_index.py`

Purpose: Compute feature embeddings for all satellite patches and build a FAISS index for fast retrieval.

Implementation:
- Load a pretrained ResNet-50 (torchvision, ImageNet weights).
- Remove the classification head. Use the output of the global average pooling layer as the embedding (2048-dim vector).
- For each satellite patch: load image, resize to 224x224, normalize with ImageNet stats, forward pass through ResNet-50, extract embedding.
- Build a FAISS IndexFlatIP (inner product, after L2-normalizing embeddings) or IndexIVFFlat for larger datasets.
- Save the index to `data/faiss_index/satellite.index`.
- Save the mapping from FAISS index position to (lat, lon) as `data/faiss_index/index_to_coords.json`.
- Print: total vectors indexed, index size on disk, sample query time.

Note: This is the BASELINE index using pretrained features. After training the Siamese model in Phase 2, this script will be re-run with the trained feature extractor to produce a better index.

#### 1E: `generate_imu_data.py`

Purpose: Generate realistic synthetic IMU data (accelerometer + gyroscope) for simulated drone flights.

Implementation:
- Define a flight path as a sequence of (lat, lon, alt, heading, speed, timestamp) waypoints along a predefined route through the region.
- Generate true velocity and orientation at each timestep (10Hz IMU rate).
- Add realistic noise models:
  - Accelerometer: bias instability (0.04 mg), velocity random walk (0.07 m/s/sqrt(hr)), white noise
  - Gyroscope: bias instability (1 deg/hr), angle random walk (0.15 deg/sqrt(hr)), white noise
- Save as `data/processed/imu_data/flight_{id}.csv` with columns: `timestamp, ax, ay, az, gx, gy, gz, true_lat, true_lon, true_alt, true_heading`.
- Generate 10 flights with different paths through the region.
- Print: total flight hours simulated, max drift at end of each flight without correction.

Deliverable: Running `make download-data && make process-data` produces all satellite patches, drone views, training pairs, FAISS index, and IMU data. The manifest CSVs are populated and correct.

---

### PHASE 2: MODEL TRAINING

Build the neural network and training pipeline in `model/`.

#### 2A: `model/config.py`

A single config dataclass or dict containing all hyperparameters:

```python
@dataclass
class TrainConfig:
    backbone: str = "resnet50"         # pretrained backbone
    embedding_dim: int = 512           # final embedding dimension (project from 2048)
    image_size: int = 224              # input image size
    batch_size: int = 64
    num_epochs: int = 50
    learning_rate: float = 3e-4
    weight_decay: float = 1e-4
    temperature: float = 0.07         # InfoNCE temperature
    num_negatives: int = 5            # hard negatives per positive pair
    margin: float = 0.5               # for triplet loss variant
    loss_type: str = "infonce"        # "infonce" or "triplet"
    train_split: float = 0.8
    val_split: float = 0.1
    test_split: float = 0.1
    checkpoint_dir: str = "model/checkpoints"
    device: str = "cuda"              # falls back to "cpu" if unavailable
```

#### 2B: `model/architectures/feature_extractor.py`

Purpose: A shared feature extractor that maps an image to a fixed-size embedding.

Implementation:
- Load ResNet-50 pretrained on ImageNet.
- Remove the final FC layer.
- Add a projection head: Linear(2048, 512) -> BatchNorm -> ReLU -> Linear(512, `embedding_dim`) -> L2 normalize.
- The projection head is trainable. The ResNet backbone has its first 6 layers frozen, remaining layers fine-tuned.
- Forward pass: image (B, 3, 224, 224) -> embedding (B, embedding_dim), L2-normalized.

#### 2C: `model/architectures/siamese_net.py`

Purpose: Siamese network with two weight-sharing branches.

Implementation:
- Uses the same `FeatureExtractor` for both branches.
- `forward(drone_image, satellite_image)` returns `(drone_embedding, satellite_embedding)`.
- Also expose `encode_drone(image)` and `encode_satellite(image)` for single-branch inference.

#### 2D: `model/losses/contrastive.py`

Purpose: InfoNCE contrastive loss.

Implementation:
- Given a batch of (drone_embedding, satellite_embedding) pairs:
  - Compute similarity matrix: `sim = drone_embeddings @ satellite_embeddings.T / temperature`
  - Labels are the diagonal (each drone view should match its corresponding satellite patch)
  - Loss = CrossEntropyLoss on the similarity matrix with diagonal labels
- Also implement triplet loss as an alternative:
  - `loss = max(0, ||anchor - positive||^2 - ||anchor - negative||^2 + margin)`

#### 2E: `model/train.py`

Purpose: Full training loop.

Implementation:
- Load training pairs CSV.
- Create a PyTorch Dataset that loads (drone_view, satellite_patch) image pairs.
- Apply training augmentations: RandomHorizontalFlip, ColorJitter, RandomGrayscale(p=0.1).
- Split into train/val/test sets.
- Training loop:
  - Forward pass through Siamese network
  - Compute InfoNCE loss
  - Backprop, optimizer step (AdamW)
  - Log: loss, top-1 retrieval accuracy, top-5 retrieval accuracy per epoch
  - Validate every epoch: compute recall@1 and recall@5 on val set
  - Save best checkpoint by val recall@1
  - Early stopping with patience=10
- Save final model to `model/checkpoints/best_model.pt`.
- Print training summary: final train loss, val recall@1, val recall@5, total training time.

#### 2F: `model/evaluate.py`

Purpose: Evaluate the trained model on the test set.

Implementation:
- Load best checkpoint.
- Re-build the FAISS index using the TRAINED feature extractor (not the pretrained one). Save to `data/faiss_index/trained_satellite.index`.
- For each test drone view:
  - Compute embedding with the drone branch.
  - Query the trained FAISS index for top-1, top-5, top-10 matches.
  - Compute localization error in meters (haversine distance between predicted and true coordinates).
- Report:
  - Median localization error (meters)
  - Mean localization error (meters)
  - Recall@1 at thresholds: 500m, 1km, 2.5km, 5km
  - Recall@5 at same thresholds
  - Error distribution histogram (save as PNG)
  - Confusion cases: show worst 10 predictions with drone view, predicted match, true match side by side (save as PNG grid)

#### 2G: `model/ekf.py`

Purpose: Extended Kalman Filter for fusing visual position estimates with IMU dead-reckoning.

Implementation:
- State vector: [lat, lon, velocity_north, velocity_east, heading]
- Prediction step (IMU update):
  - Use accelerometer and gyroscope readings to propagate position and velocity.
  - Apply process noise based on IMU noise characteristics.
- Update step (visual fix):
  - When a visual geo-localization estimate is available, update the state with the measurement.
  - Measurement noise is inversely proportional to the visual match confidence score.
  - High confidence (>0.8): measurement noise = 50m
  - Medium confidence (0.5-0.8): measurement noise = 200m
  - Low confidence (<0.5): measurement noise = 1000m (essentially ignored)
- Output: filtered (lat, lon), confidence ellipse (2x2 covariance matrix), innovation (difference between predicted and measured).
- Expose a `step(imu_reading, visual_estimate=None, visual_confidence=None)` method that returns the full state and covariance.

#### 2H: `model/inference.py`

Purpose: End-to-end inference pipeline combining geo-localization and EKF.

Implementation:
- Load trained model and FAISS index.
- Initialize EKF with a starting position.
- `process_frame(drone_image, imu_readings)`:
  1. Compute drone image embedding.
  2. Query FAISS index for top-5 matches.
  3. Compute confidence as the ratio of top-1 similarity to top-2 similarity (distinctiveness).
  4. If confidence > threshold (0.3), pass visual estimate to EKF update step.
  5. Always run EKF prediction step with IMU data.
  6. Return: estimated position, confidence, top-5 matches with scores, EKF state, raw visual estimate, IMU-only estimate.
- This is the function the API will call.

Deliverable: Running `make train` trains the model and saves checkpoints. Running `make evaluate` produces error metrics and visualizations. The trained FAISS index is rebuilt with learned features.

---

### PHASE 3: API SERVER

Build the FastAPI backend in `api/`.

#### 3A: `api/schemas.py`

Pydantic models:

```python
class PositionEstimate(BaseModel):
    lat: float
    lon: float
    confidence: float               # 0-1
    error_radius_m: float           # confidence ellipse radius in meters
    source: str                     # "visual", "imu", "fused"

class MatchResult(BaseModel):
    satellite_patch_path: str
    lat: float
    lon: float
    similarity_score: float

class FrameResponse(BaseModel):
    timestamp: float
    estimated_position: PositionEstimate
    ground_truth: Optional[PositionEstimate]
    top_matches: List[MatchResult]  # top 5
    imu_only_position: PositionEstimate
    visual_only_position: Optional[PositionEstimate]
    ekf_state: dict                 # full state vector and covariance
    metrics: dict                   # error_m, drift_m, confidence_history

class SimulationConfig(BaseModel):
    flight_id: int = 0
    speed: float = 1.0              # playback speed multiplier
    gps_jammed: bool = True
    camera_noise: float = 0.0       # 0-1, amount of synthetic noise
    altitude_m: float = 200.0
    region: str = "donetsk"
```

#### 3B: `api/simulation.py`

Purpose: A simulation engine that replays a pre-generated flight, frame by frame.

Implementation:
- Load a flight's IMU data and the corresponding sequence of drone views.
- On each tick (configurable rate, default 2Hz for visual frames, 10Hz for IMU):
  - Get the current drone view image and IMU readings.
  - Call `model/inference.py` `process_frame()`.
  - Package the result as a `FrameResponse`.
  - If `camera_noise > 0`, add Gaussian noise to the drone view before processing.
  - Track cumulative metrics: total drift, running error, confidence history.
- Expose `start()`, `stop()`, `step()`, `get_state()` methods.

#### 3C: `api/ws_manager.py`

Purpose: WebSocket connection manager for streaming simulation results to the frontend.

Implementation:
- Manage multiple WebSocket connections.
- On connection: start a simulation instance.
- Stream `FrameResponse` JSON to the client at the configured rate.
- Accept control messages from the client: `{"action": "set_speed", "value": 2.0}`, `{"action": "toggle_jamming"}`, `{"action": "set_noise", "value": 0.5}`, `{"action": "restart"}`.

#### 3D: `api/main.py`

Purpose: FastAPI application.

Endpoints:
- `GET /health` — returns status, model loaded, index size
- `POST /localize` — accepts a drone image (base64 or file upload), returns single-frame position estimate. For testing without the full simulation.
- `GET /flights` — returns list of available pre-generated flights with metadata
- `GET /regions` — returns available regions with bounding boxes
- `WS /ws/simulate` — WebSocket endpoint that streams simulation frames
- `GET /demo` — returns a pre-recorded simulation run as a JSON array of FrameResponse objects (for static demo without running inference)

On startup:
- Load trained model.
- Load FAISS index.
- Load coordinate mapping.
- Pre-generate a demo run and cache it.

Deliverable: Running `make serve-api` starts the FastAPI server on port 8000. The `/demo` endpoint returns valid data. The WebSocket endpoint streams simulation frames.

---

### PHASE 4: FRONTEND

Build the Next.js application in `frontend/`.

#### 4A: Layout and Theme

`src/app/layout.tsx`:
- Full viewport height, no scroll.
- Import Inter and JetBrains Mono fonts.
- Dark theme using the color palette defined above.
- Set page title: "ARIADNE | GPS-Denied Visual Navigation"

`src/app/globals.css`:
- CSS custom properties for all design tokens (colors, fonts, spacing).
- Smooth scrolling disabled (single viewport app).
- Custom scrollbar styling (thin, dark).
- Glow effects: `box-shadow: 0 0 20px rgba(59, 130, 246, 0.15)` for active elements.

`src/app/page.tsx`:
- Three-panel layout using CSS Grid:
  ```
  grid-template-columns: 320px 1fr 360px
  grid-template-rows: 56px 1fr
  ```
- Row 1: ControlBar (spans all columns)
- Row 2, Col 1: DroneViewPanel
- Row 2, Col 2: MapPanel
- Row 2, Col 3: TelemetryPanel
- On mobile (< 1024px): stack panels vertically with tab navigation at the bottom.

#### 4B: ControlBar Component

Location: `src/components/ControlBar.tsx`

A horizontal bar at the top of the viewport. Contains:
- Left: ARIADNE logo (the word "ARIADNE" in Inter 600 weight, with a small thread icon from Lucide). Below it in zinc-500 text: "GPS-DENIED VISUAL NAVIGATION".
- Center: Playback controls:
  - Play/Pause button (Lucide Play/Pause icons)
  - Speed selector: 0.5x, 1x, 2x, 4x (segmented button group)
  - Progress bar showing simulation progress (thin, blue-500)
- Right: Control toggles:
  - "GPS JAMMED" toggle (shadcn Switch component). When ON, the switch glows red. When OFF, glows green. Default: ON.
  - "CAMERA NOISE" slider (shadcn Slider, 0-100%). Shows current value.
  - "ALTITUDE" dropdown: 100m, 200m, 300m, 500m.
  - Region selector dropdown (if multiple regions available).

Styling: Background `#0f1117`, bottom border `#1e2130`, height exactly 56px, items vertically centered.

#### 4C: DroneViewPanel (Left Panel)

Location: `src/components/DroneViewPanel.tsx`

Top section (60% of panel height): DRONE CAMERA FEED
- Displays the current drone camera frame as an image.
- Overlaid in the top-left corner: current altitude, heading, and speed in JetBrains Mono.
- If GPS is jammed, show a pulsing red "GPS DENIED" badge in the top-right corner.
- If camera noise is applied, the image should visually show the noise.
- Subtle animated scanline effect (CSS animation, very faint horizontal lines moving downward, opacity 0.03) to give a camera-feed feel without being distracting.

Bottom section (40% of panel height): TOP MATCHES
- Header: "REFERENCE MATCHES" in zinc-500 uppercase, 11px.
- Show top 3 satellite patch matches as `MatchCard` components in a horizontal row.
- Each `MatchCard` shows:
  - The satellite patch image (small, 80x80px).
  - Similarity score as a percentage (e.g., "94.2%").
  - Distance from estimated position in km.
  - A colored border: green if score > 0.85, amber if 0.6-0.85, red if < 0.6.
  - The #1 match has a subtle blue glow border.

#### 4D: MapPanel (Center Panel)

Location: `src/components/MapPanel.tsx`

A full-height Mapbox GL JS map using the `mapbox://styles/mapbox/satellite-streets-v12` style (satellite imagery with labels).

Map elements:
1. ESTIMATED PATH: A line rendered as a GeoJSON LineString, colored blue-500 (#3b82f6), with a glow effect (achieved by rendering a wider, semi-transparent line underneath). Updated in real time as new position estimates arrive.

2. GROUND TRUTH PATH: A dashed line, colored amber-500 (#f59e0b), opacity 0.7. Only shown if ground truth is available.

3. CURRENT POSITION: A pulsing dot at the latest estimated position. Use a custom Mapbox marker with CSS animation:
   - Outer ring: 24px, blue-400, opacity pulsing between 0.2 and 0.6.
   - Inner dot: 8px, solid blue-500.

4. CONFIDENCE RADIUS: A translucent circle centered on the current position. Radius = `error_radius_m` from the API. Fill: blue-500 at 10% opacity. Stroke: blue-500 at 30% opacity. This circle grows when confidence drops and shrinks when a strong visual match is made.

5. GPS JAMMING ZONE: When GPS is jammed, render a semi-transparent red rectangle over the flight area with diagonal hash lines (CSS pattern). Label: "EW ACTIVE" in red-500.

6. MATCH LINE: A thin dashed white line connecting the current position dot to the matched satellite patch location (showing where the system thinks it is vs. where the best match is).

Map behavior:
- Camera follows the drone position with smooth animation (`flyTo` with duration 1000ms).
- Zoom level auto-adjusts based on altitude (higher altitude = more zoomed out).
- Allow user to freely pan/zoom, with a "recenter" button (Lucide Crosshair icon) in the bottom-right to snap back to following the drone.

Bottom overlay on the map: A frosted-glass bar (backdrop-blur-md, bg-surface/80) showing:
- Current error: "ERROR: 127m" in large JetBrains Mono text. Color-coded: green < 200m, amber 200-500m, red > 500m.
- Current mode: "VISUAL-INERTIAL" or "IMU ONLY" (when no visual match is confident enough).
- Elapsed time of the simulation.

#### 4E: TelemetryPanel (Right Panel)

Location: `src/components/TelemetryPanel.tsx`

Scrollable panel with the following sections, stacked vertically:

Section 1: POSITION READOUT
- A card with dark surface background.
- Header: "ESTIMATED POSITION" in zinc-500 uppercase, 11px.
- Two rows in JetBrains Mono 14px:
  - `LAT  48.XXXXXX°N`
  - `LON  37.XXXXXX°E`
- Below: `ALT  200m  |  HDG  045°  |  SPD  12 m/s`
- All values update in real time with a subtle number-flip animation (Framer Motion `AnimatePresence` with `layout` prop).

Section 2: ERROR CHART
- A Recharts `LineChart` (200px height) showing position error (meters) over time.
- X-axis: time (seconds). Y-axis: error (meters).
- Two lines:
  - Blue: fused (EKF) error
  - Red dashed: IMU-only error (showing how bad drift would be without visual correction)
- Background reference bands: green zone (0-200m), amber zone (200-500m), red zone (500m+).
- When a strong visual match occurs, show a small green dot on the blue line (visual fix event).

Section 3: CONFIDENCE CHART
- A Recharts `AreaChart` (150px height) showing visual match confidence over time.
- Fill: gradient from blue-500 (bottom) to transparent (top).
- A horizontal dashed line at 0.3 (the threshold below which visual estimates are rejected).
- Label: "MATCH THRESHOLD" next to the line.

Section 4: FILTER STATE
- Header: "SENSOR FUSION"
- A horizontal stacked bar showing the current EKF weighting:
  - Blue portion: "VISUAL" weight percentage
  - Amber portion: "IMU" weight percentage
- Updates in real time. When GPS is jammed and no visual match is available, the bar goes 100% amber. When a strong match comes in, blue portion jumps.

Section 5: SESSION STATS
- A small stats grid (2x3):
  - "FRAMES" — total frames processed
  - "FIXES" — number of successful visual fixes
  - "AVG ERROR" — running average error in meters
  - "MAX DRIFT" — maximum IMU drift before correction
  - "FIX RATE" — percentage of frames with visual fix > threshold
  - "RUNTIME" — elapsed time

#### 4F: Hooks

`src/hooks/useWebSocket.ts`:
- Connect to `ws://localhost:8000/ws/simulate`.
- Parse incoming `FrameResponse` JSON.
- Maintain a state buffer of the last 500 frames for chart rendering.
- Expose: `isConnected`, `currentFrame`, `frameHistory`, `sendControl(action, value)`.
- Auto-reconnect on disconnect with exponential backoff.

`src/hooks/useSimulation.ts`:
- Wraps `useWebSocket`.
- Exposes: `play()`, `pause()`, `setSpeed()`, `toggleJamming()`, `setNoise()`, `restart()`.
- Maintains derived state: `currentError`, `totalDrift`, `fixCount`, `isJammed`.
- If WebSocket is not available, falls back to loading pre-recorded demo data from `/demo/simulation.json` and replaying it client-side with `requestAnimationFrame`.

#### 4G: Demo Data Fallback

For GitHub visitors who just want to see the app work without running the backend:
- Pre-generate a full simulation run (1000 frames) and save as `frontend/public/demo/simulation.json`.
- The `useSimulation` hook detects if the WebSocket connection fails and automatically switches to demo mode.
- Demo mode replays the pre-recorded frames at the configured speed.
- All UI components work identically in demo mode and live mode.

Deliverable: Running `make serve-frontend` starts the Next.js app on port 3000. The UI renders all three panels. In demo mode (no backend), it replays pre-recorded data with full interactivity.

---

### PHASE 5: INTEGRATION AND DEMO

#### 5A: End-to-End Test

1. Start the API server: `make serve-api`
2. Start the frontend: `make serve-frontend`
3. Open http://localhost:3000
4. The simulation should auto-play, streaming frames from the backend.
5. Verify:
   - Drone camera feed updates in the left panel.
   - Map shows the trajectory growing in real time.
   - Telemetry charts update.
   - Toggling "GPS JAMMED" changes the system behavior visibly.
   - Changing camera noise degrades match confidence visibly.
   - The error chart shows IMU drift growing and then snapping back when visual fixes occur.

#### 5B: Pre-Record Demo Data

Run the simulation once and save all FrameResponse objects to `frontend/public/demo/simulation.json`. This ensures the GitHub Pages / Vercel deployment works without the Python backend.

#### 5C: README.md

The README must contain:

1. A hero section with:
   - Project name and tagline
   - A high-quality demo GIF or embedded video (record the UI in action, 15-20 seconds, showing the map trajectory growing, a visual fix snapping the position, and the telemetry updating)
   - One-sentence description: "ARIADNE is a visual-inertial navigation system that enables autonomous drones to determine their position using terrain matching when GPS is denied."

2. "Why This Exists" section (3-4 sentences):
   - Reference Ukraine's Ministry of Defence goal of equipping 100% of frontline drones with computer vision navigation.
   - Reference the GPS jamming/spoofing problem documented by CSIS, Forbes, and Ukrainian officials.
   - State that this is a proof-of-concept built with public data, not classified information.

3. Architecture diagram (Mermaid or image):
   - Show: Satellite Imagery -> Patch Database -> FAISS Index -> Geo-Localization Model <- Drone Camera Feed -> EKF Fusion <- IMU Data -> Position Estimate -> Frontend Visualization

4. "Quick Start" section with exact commands:
   ```
   git clone https://github.com/YOUR_USERNAME/ariadne.git
   cd ariadne
   cp .env.example .env        # add your API keys
   make setup                  # install dependencies
   make download-data          # get satellite imagery
   make process-data           # generate patches and training pairs
   make train                  # train the geo-localization model
   make serve-api              # start backend on :8000
   make serve-frontend         # start frontend on :3000
   ```

5. "Demo Mode" section: explain that the frontend works without the backend by replaying pre-recorded data.

6. "Results" section with:
   - Median localization error achieved
   - Recall@1 at 1km threshold
   - A screenshot of the error distribution histogram
   - A screenshot of the full UI in action

7. "How It Works" section with brief explanations of each module (2-3 sentences each, not paragraphs).

8. Tech stack badges (Python, PyTorch, FastAPI, Next.js, Mapbox, FAISS).

9. License: MIT.

#### 5D: Jupyter Notebook

`notebooks/walkthrough.ipynb` must walk through:
1. Loading and visualizing a satellite patch.
2. Generating a synthetic drone view from it.
3. Computing embeddings for both and showing cosine similarity.
4. Querying the FAISS index and showing top-5 results visually.
5. Running the EKF on a short flight segment and plotting filtered vs. unfiltered position.
6. Showing error metrics on the test set.

Each cell should have markdown explanations above it. Include inline plots (matplotlib). This notebook is for recruiters and engineers who want to understand the system without reading all the code.

---

### PHASE 6: DEPLOYMENT AND POLISH

#### 6A: Docker

`docker-compose.yml` should allow `docker-compose up` to start the full stack (API + frontend) with no manual setup beyond providing API keys in `.env`.

#### 6B: Vercel Deployment

The frontend should be deployable to Vercel with zero config. In demo mode (no backend), it serves the pre-recorded simulation data. Add `vercel.json` if needed.

#### 6C: GitHub Actions (optional but impressive)

Add `.github/workflows/test.yml`:
- Run Python unit tests (model forward pass, EKF step, FAISS query).
- Run frontend build check (`next build`).
- Badge in README showing passing tests.

---

## CRITICAL IMPLEMENTATION NOTES

1. The FAISS index MUST be rebuilt after training. The pretrained ResNet-50 features (Phase 1D) are a baseline. The trained Siamese features (Phase 2F) will produce a significantly better index. The API must use the trained index.

2. The EKF is what makes this project non-trivial. Without it, you just have image retrieval. With it, you have a navigation system. The EKF should visibly improve accuracy compared to visual-only or IMU-only estimates. The telemetry panel should make this obvious.

3. The demo mode fallback is critical. Most people who find this on GitHub will not set up a Python ML backend. If they can open the Vercel link and see it working immediately, that's 10x more impact than a repo that requires 30 minutes of setup.

4. The UI must not look like a generic dashboard template. The dark theme, the specific color palette, the military-inspired typography (JetBrains Mono for readouts), the pulsing position dot, the confidence radius circle, the scanline effect on the camera feed: these details signal craft. Do not use default Tailwind colors or shadcn defaults without overriding them to match the palette above.

5. Error handling: if satellite imagery download fails, if model training produces NaN losses, if FAISS index is empty, if WebSocket disconnects: every failure mode should produce a clear error message and a fallback behavior, not a crash.

6. All scripts must have `if __name__ == "__main__":` blocks with argparse for CLI usage, AND be importable as modules for use in other scripts.

7. The training script must work on CPU (slowly) for users without GPUs. Detect CUDA availability and fall back gracefully. Print estimated training time at the start.

---

## EVALUATION CRITERIA (what "done" looks like)

- [ ] `make setup` installs everything in under 5 minutes
- [ ] `make process-data` generates at least 10,000 training pairs
- [ ] `make train` completes without errors and saves a checkpoint
- [ ] `make evaluate` reports median localization error < 2km (achievable target for this approach)
- [ ] `make serve-api` starts and responds to `/health` and `/demo`
- [ ] `make serve-frontend` starts and renders all three panels
- [ ] Demo mode works without the backend
- [ ] Toggling GPS jamming visibly changes the UI behavior
- [ ] The error chart shows IMU drift growing between visual fixes
- [ ] The README contains a demo GIF and architecture diagram
- [ ] The Jupyter notebook runs end-to-end
- [ ] `docker-compose up` starts the full stack