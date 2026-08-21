"use client";

import type { FrameResponse } from "@/lib/types";
import { MatchCard } from "./MatchCard";

function haversineKm(
  lat1: number,
  lon1: number,
  lat2: number,
  lon2: number
): number {
  const R = 6371;
  const p1 = (lat1 * Math.PI) / 180;
  const p2 = (lat2 * Math.PI) / 180;
  const dp = ((lat2 - lat1) * Math.PI) / 180;
  const dl = ((lon2 - lon1) * Math.PI) / 180;
  const a =
    Math.sin(dp / 2) ** 2 +
    Math.cos(p1) * Math.cos(p2) * Math.sin(dl / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(a));
}

interface Props {
  frame: FrameResponse | null;
  noise: number;
}

export function DroneViewPanel({ frame, noise }: Props) {
  const imgSrc = frame?.drone_image_b64
    ? `data:image/jpeg;base64,${frame.drone_image_b64}`
    : null;
  const est = frame?.estimated_position;
  const matches = frame?.top_matches?.slice(0, 3) ?? [];

  return (
    <aside className="flex h-full flex-col border-r border-border bg-surface">
      <div className="relative flex-[0.6] overflow-hidden border-b border-border">
        <div className="absolute inset-0 bg-background">
          {imgSrc ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={imgSrc}
              alt="Drone camera"
              className="h-full w-full object-cover"
              style={{ filter: noise > 0 ? `contrast(${1 - noise * 0.4})` : undefined }}
            />
          ) : (
            <div
              className="h-full w-full"
              style={{
                background:
                  "radial-gradient(ellipse at 40% 40%, #1e3a5f 0%, #0f1117 55%, #06060a 100%)",
              }}
            />
          )}
          <div className="scanlines pointer-events-none absolute inset-0" />
        </div>

        <div className="absolute left-2 top-2 space-y-0.5 font-mono text-[11px] text-text-primary drop-shadow">
          <div>ALT {Math.round(frame?.altitude_m ?? 200)}m</div>
          <div>HDG {Math.round(frame?.heading ?? 0).toString().padStart(3, "0")}°</div>
          <div>SPD {(frame?.speed_mps ?? 12).toFixed(1)} m/s</div>
        </div>

        {(frame?.gps_jammed ?? true) && (
          <div className="absolute right-2 top-2 animate-pulse rounded border border-error bg-error/20 px-2 py-1 font-mono text-[10px] font-semibold text-error">
            GPS DENIED
          </div>
        )}
      </div>

      <div className="flex flex-[0.4] flex-col gap-2 p-3">
        <div className="text-[11px] uppercase tracking-wider text-text-secondary">
          Reference Matches
        </div>
        <div className="flex gap-2">
          {matches.length === 0 && (
            <div className="text-[11px] text-text-muted">Awaiting matches…</div>
          )}
          {matches.map((m, i) => (
            <MatchCard
              key={`${m.satellite_patch_path}-${i}`}
              score={m.similarity_score}
              distanceKm={
                est
                  ? haversineKm(est.lat, est.lon, m.lat, m.lon)
                  : 0
              }
              rank={i}
              label={m.satellite_patch_path}
            />
          ))}
        </div>
      </div>
    </aside>
  );
}
