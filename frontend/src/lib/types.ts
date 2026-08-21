export interface PositionEstimate {
  lat: number;
  lon: number;
  confidence: number;
  error_radius_m: number;
  source: string;
}

export interface MatchResult {
  satellite_patch_path: string;
  lat: number;
  lon: number;
  similarity_score: number;
}

export interface FrameResponse {
  timestamp: number;
  estimated_position: PositionEstimate;
  ground_truth?: PositionEstimate | null;
  top_matches: MatchResult[];
  imu_only_position: PositionEstimate;
  visual_only_position?: PositionEstimate | null;
  ekf_state: Record<string, unknown>;
  metrics: {
    error_m?: number;
    imu_error_m?: number;
    drift_m?: number;
    frames?: number;
    fixes?: number;
    avg_error?: number;
    max_drift?: number;
    fix_rate?: number;
    runtime?: number;
    visual_fix?: boolean;
    confidence_history?: number[];
  };
  drone_image_b64?: string | null;
  altitude_m: number;
  heading: number;
  speed_mps: number;
  gps_jammed: boolean;
  mode: string;
}
