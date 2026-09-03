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
  const hdg = Math.round(frame?.heading ?? 0)
    .toString()
    .padStart(3, "0");

  return (
    <aside className="flex h-full flex-col border-r border-border bg-surface">
      <div className="panel-header">
        <div className="flex items-center gap-2">
          <span className="status-dot bg-estimated" />
          <span className="panel-title">DRONE FEED · CAM-01</span>
        </div>
        <span className="font-mono text-[9px] tracking-widest text-text-muted">
          1280 × 720 · 30 FPS
        </span>
      </div>

      <div className="relative flex-[0.55] overflow-hidden border-b border-border">
        <div className="absolute inset-0 bg-background">
          {imgSrc ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={imgSrc}
              alt="Drone camera"
              className="h-full w-full object-cover"
              style={{
                filter: noise > 0 ? `contrast(${1 - noise * 0.4})` : undefined,
              }}
            />
          ) : (
            <div
              className="h-full w-full"
              style={{
                background:
                  "radial-gradient(ellipse at 40% 40%, #142238 0%, #0b0d12 55%, #07080b 100%)",
              }}
            />
          )}
          <div className="scanlines pointer-events-none absolute inset-0" />
          <div className="pointer-events-none absolute inset-0 grid-overlay opacity-40" />

          <div className="pointer-events-none absolute inset-0">
            <div className="absolute left-3 top-3 h-3 w-3 border-l border-t border-white/40" />
            <div className="absolute right-3 top-3 h-3 w-3 border-r border-t border-white/40" />
            <div className="absolute left-3 bottom-3 h-3 w-3 border-l border-b border-white/40" />
            <div className="absolute right-3 bottom-3 h-3 w-3 border-r border-b border-white/40" />
            <div className="absolute left-1/2 top-1/2 h-5 w-5 -translate-x-1/2 -translate-y-1/2 border border-estimated/60" />
            <div className="absolute left-1/2 top-1/2 h-px w-8 -translate-x-1/2 -translate-y-1/2 bg-estimated/40" />
            <div className="absolute left-1/2 top-1/2 h-8 w-px -translate-x-1/2 -translate-y-1/2 bg-estimated/40" />
          </div>
        </div>

        <div className="absolute left-3 top-3 space-y-0.5 font-mono text-[10px] leading-tight text-white drop-shadow">
          <div className="flex gap-1.5">
            <span className="text-text-muted">ALT</span>
            <span>{Math.round(frame?.altitude_m ?? 200)}M</span>
          </div>
          <div className="flex gap-1.5">
            <span className="text-text-muted">HDG</span>
            <span>{hdg}°</span>
          </div>
          <div className="flex gap-1.5">
            <span className="text-text-muted">SPD</span>
            <span>{(frame?.speed_mps ?? 12).toFixed(1)} M/S</span>
          </div>
        </div>

        <div className="absolute right-3 top-3 space-y-1 text-right font-mono text-[10px] text-white/80">
          <div>{new Date().toISOString().slice(11, 19)}Z</div>
          <div className="text-text-muted">T+{(frame?.timestamp ?? 0).toFixed(1)}S</div>
        </div>

        {(frame?.gps_jammed ?? true) && (
          <div className="absolute left-1/2 top-14 -translate-x-1/2 animate-pulse border border-error/70 bg-error/15 px-2.5 py-0.5 font-mono text-[10px] font-semibold tracking-widest text-error backdrop-blur-sm">
            ⚠ GPS DENIED · EW ACTIVE
          </div>
        )}

        <div className="absolute bottom-3 left-3 right-3 flex items-end justify-between font-mono text-[9px] text-white/70">
          <div className="flex flex-col gap-0.5">
            <span className="text-text-muted">SENSOR</span>
            <span>EO/NIR</span>
          </div>
          <div className="flex flex-col items-end gap-0.5">
            <span className="text-text-muted">SIGNAL</span>
            <div className="flex gap-0.5">
              {[1, 2, 3, 4, 5].map((i) => (
                <span
                  key={i}
                  className={`h-2 w-1 ${i <= 3 ? "bg-confident" : "bg-white/20"}`}
                />
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="flex flex-[0.45] flex-col gap-2 p-3">
        <div className="flex items-center justify-between">
          <span className="panel-title">Reference Matches · Top 3</span>
          <span className="font-mono text-[9px] tracking-widest text-text-muted">
            FAISS · L2
          </span>
        </div>
        <div className="flex gap-2">
          {matches.length === 0 && (
            <div className="font-mono text-[10px] uppercase tracking-widest text-text-muted">
              Awaiting matches…
            </div>
          )}
          {matches.map((m, i) => (
            <MatchCard
              key={`${m.satellite_patch_path}-${i}`}
              score={m.similarity_score}
              distanceKm={
                est ? haversineKm(est.lat, est.lon, m.lat, m.lon) : 0
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
