"""Pydantic schemas for ARIADNE API."""

from __future__ import annotations

from typing import Any, List, Optional

from pydantic import BaseModel, Field


class PositionEstimate(BaseModel):
    lat: float
    lon: float
    confidence: float
    error_radius_m: float
    source: str  # visual | imu | fused


class MatchResult(BaseModel):
    satellite_patch_path: str
    lat: float
    lon: float
    similarity_score: float


class FrameResponse(BaseModel):
    timestamp: float
    estimated_position: PositionEstimate
    ground_truth: Optional[PositionEstimate] = None
    top_matches: List[MatchResult] = Field(default_factory=list)
    imu_only_position: PositionEstimate
    visual_only_position: Optional[PositionEstimate] = None
    ekf_state: dict = Field(default_factory=dict)
    metrics: dict = Field(default_factory=dict)
    drone_image_b64: Optional[str] = None
    altitude_m: float = 200.0
    heading: float = 0.0
    speed_mps: float = 12.0
    gps_jammed: bool = True
    mode: str = "VISUAL-INERTIAL"


class SimulationConfig(BaseModel):
    flight_id: int = 0
    speed: float = 1.0
    gps_jammed: bool = True
    camera_noise: float = 0.0
    altitude_m: float = 200.0
    region: str = "donetsk"


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    index_size: int
    version: str = "0.1.0"


class LocalizeResponse(BaseModel):
    estimated_position: PositionEstimate
    top_matches: List[MatchResult]
    ekf_state: dict
    metrics: dict = Field(default_factory=dict)
