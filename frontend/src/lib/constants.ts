export const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
export const WS_URL =
  process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";
export const MAPBOX_TOKEN =
  process.env.NEXT_PUBLIC_MAPBOX_ACCESS_TOKEN || "";

export const SPEEDS = [0.5, 1, 2, 4] as const;
export const ALTITUDES = [100, 200, 300, 500] as const;
export const MATCH_THRESHOLD = 0.3;
export const HISTORY_LIMIT = 500;

export const DEFAULT_CENTER: [number, number] = [37.95, 48.4]; // lon, lat
