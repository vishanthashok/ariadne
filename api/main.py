"""FastAPI application for ARIADNE inference and simulation."""

from __future__ import annotations

import base64
import io
import json
import sys
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")

from api.schemas import (
    FrameResponse,
    HealthResponse,
    LocalizeResponse,
    MatchResult,
    PositionEstimate,
    SimulationConfig,
)
from api.simulation import SimulationEngine
from api.ws_manager import manager, simulation_loop
from model.inference import AriadneInference

app = FastAPI(title="ARIADNE API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

inference_engine = AriadneInference()
_demo_cache: list[dict] | None = None


def _load_or_build_demo() -> list[dict]:
    global _demo_cache
    if _demo_cache is not None:
        return _demo_cache
    demo_path = ROOT / "frontend" / "public" / "demo" / "simulation.json"
    if demo_path.exists():
        _demo_cache = json.loads(demo_path.read_text(encoding="utf-8"))
        return _demo_cache
    engine = SimulationEngine(SimulationConfig())
    frames = engine.run_all(max_frames=200)
    # strip heavy images for API demo endpoint lightness if needed
    _demo_cache = frames
    return _demo_cache


@app.on_event("startup")
async def startup() -> None:
    try:
        _load_or_build_demo()
        print("Demo cache ready")
    except Exception as e:
        print(f"Demo cache deferred: {e}")


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    index_size = len(inference_engine.mapping) if inference_engine.mapping else 0
    return HealthResponse(
        status="ok",
        model_loaded=inference_engine.loaded,
        index_size=index_size,
    )


@app.post("/localize", response_model=LocalizeResponse)
async def localize(file: UploadFile = File(...)) -> LocalizeResponse:
    data = await file.read()
    img = Image.open(io.BytesIO(data)).convert("RGB")
    imu = {"ax": 0.0, "ay": 0.0, "az": 9.81, "gx": 0.0, "gy": 0.0, "gz": 0.0}
    result = inference_engine.process_frame(img, imu)
    visual = result.get("visual_only_position")
    return LocalizeResponse(
        estimated_position=PositionEstimate(**result["estimated_position"]),
        top_matches=[MatchResult(**m) for m in result.get("top_matches", [])],
        ekf_state=result.get("ekf_state", {}),
        metrics={"confidence": result.get("confidence", 0)},
    )


@app.get("/flights")
def flights() -> list[dict]:
    imu_dir = ROOT / "data" / "processed" / "imu_data"
    out = []
    if imu_dir.exists():
        for p in sorted(imu_dir.glob("flight_*.csv")):
            fid = int(p.stem.split("_")[1])
            out.append({"flight_id": fid, "path": str(p), "region": "donetsk"})
    if not out:
        out = [{"flight_id": i, "path": "synthetic", "region": "donetsk"} for i in range(10)]
    return out


@app.get("/regions")
def regions() -> list[dict]:
    return [
        {
            "id": "donetsk",
            "name": "Donetsk Oblast",
            "bbox": [37.5, 48.0, 38.5, 48.8],
        }
    ]


@app.get("/demo")
def demo() -> JSONResponse:
    frames = _load_or_build_demo()
    return JSONResponse(frames)


@app.websocket("/ws/simulate")
async def ws_simulate(websocket: WebSocket) -> None:
    await manager.connect(websocket)
    # Optional init config from query
    config = SimulationConfig()
    engine = SimulationEngine(config)
    await simulation_loop(websocket, engine)
