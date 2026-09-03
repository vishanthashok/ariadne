"use client";

import { Pause, Play, RotateCcw } from "lucide-react";
import { ALTITUDES, SPEEDS } from "@/lib/constants";

interface Props {
  playing: boolean;
  speed: number;
  isJammed: boolean;
  noise: number;
  altitude: number;
  progress: number;
  demoMode: boolean;
  onPlay: () => void;
  onPause: () => void;
  onSpeed: (s: number) => void;
  onToggleJam: () => void;
  onNoise: (n: number) => void;
  onAltitude: (a: number) => void;
  onRestart: () => void;
}

export function ControlBar(props: Props) {
  return (
    <header className="col-span-full flex h-14 items-center gap-6 border-b border-border bg-surface px-4">
      <div className="flex min-w-[220px] items-center gap-3">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
          <rect x="2" y="2" width="20" height="20" stroke="#4c8dff" strokeWidth="1" />
          <rect x="6" y="6" width="12" height="12" stroke="#4c8dff" strokeWidth="1" strokeOpacity="0.6" />
          <rect x="10" y="10" width="4" height="4" fill="#4c8dff" />
        </svg>
        <div className="leading-tight">
          <div className="flex items-center gap-2 font-mono text-[12px] font-semibold tracking-widest text-text-primary">
            ARIADNE
            <span className="text-text-muted">/</span>
            <span className="text-[10px] font-normal text-text-secondary">MC-1</span>
          </div>
          <div className="text-[9px] uppercase tracking-widest text-text-secondary">
            Visual-Inertial Navigation Console
          </div>
        </div>
        <span className="ml-1 flex items-center gap-1.5 border border-border bg-surface-elevated px-1.5 py-0.5 font-mono text-[9px] uppercase tracking-widest text-confident">
          <span className="status-dot bg-confident" style={{ margin: 0 }} />
          {props.demoMode ? "DEMO" : "LIVE"}
        </span>
      </div>

      <div className="flex flex-1 items-center gap-3">
        <div className="flex overflow-hidden border border-border">
          <button
            type="button"
            onClick={props.playing ? props.onPause : props.onPlay}
            className="flex h-7 w-8 items-center justify-center bg-surface-elevated text-text-primary hover:bg-surface-raised"
            aria-label={props.playing ? "Pause" : "Play"}
          >
            {props.playing ? <Pause className="h-3.5 w-3.5" /> : <Play className="h-3.5 w-3.5" />}
          </button>
          <button
            type="button"
            onClick={props.onRestart}
            className="flex h-7 w-8 items-center justify-center border-l border-border bg-surface-elevated text-text-secondary hover:text-text-primary"
            aria-label="Restart"
          >
            <RotateCcw className="h-3.5 w-3.5" />
          </button>
        </div>

        <div className="flex overflow-hidden border border-border">
          {SPEEDS.map((s) => (
            <button
              key={s}
              type="button"
              onClick={() => props.onSpeed(s)}
              className={`px-2.5 py-1 font-mono text-[10px] tracking-wider ${
                props.speed === s
                  ? "bg-estimated/15 text-estimated"
                  : "bg-surface-elevated text-text-secondary hover:text-text-primary"
              }`}
            >
              {s}X
            </button>
          ))}
        </div>

        <div className="flex flex-1 items-center gap-2">
          <span className="font-mono text-[9px] uppercase tracking-widest text-text-muted">
            MISSION T
          </span>
          <div className="relative h-1 flex-1 max-w-[280px] overflow-hidden bg-border">
            <div
              className="h-full bg-estimated"
              style={{ width: `${Math.min(100, props.progress * 100)}%` }}
            />
          </div>
          <span className="font-mono text-[10px] text-text-primary">
            {(props.progress * 100).toFixed(1)}%
          </span>
        </div>
      </div>

      <div className="flex items-center gap-5">
        <div className="flex items-center gap-2">
          <span className="font-mono text-[9px] uppercase tracking-widest text-text-secondary">
            GPS
          </span>
          <button
            type="button"
            role="switch"
            aria-checked={props.isJammed}
            onClick={props.onToggleJam}
            className={`flex items-center gap-1.5 border px-2 py-1 font-mono text-[10px] tracking-widest ${
              props.isJammed
                ? "border-error/60 bg-error/10 text-error"
                : "border-confident/60 bg-confident/10 text-confident"
            }`}
          >
            <span
              className={`status-dot ${props.isJammed ? "bg-error" : "bg-confident"}`}
              style={{ margin: 0 }}
            />
            {props.isJammed ? "DENIED" : "NOMINAL"}
          </button>
        </div>

        <label className="flex flex-col gap-1 font-mono text-[9px] uppercase tracking-widest text-text-secondary">
          <div className="flex items-center justify-between gap-2">
            <span>Noise</span>
            <span className="text-text-primary">{Math.round(props.noise * 100)}%</span>
          </div>
          <input
            type="range"
            min={0}
            max={100}
            value={props.noise * 100}
            onChange={(e) => props.onNoise(Number(e.target.value) / 100)}
            className="h-1 w-24 accent-estimated"
          />
        </label>

        <label className="flex flex-col gap-1 font-mono text-[9px] uppercase tracking-widest text-text-secondary">
          <span>Altitude</span>
          <select
            value={props.altitude}
            onChange={(e) => props.onAltitude(Number(e.target.value))}
            className="border border-border bg-surface-elevated px-2 py-1 font-mono text-[10px] text-text-primary"
          >
            {ALTITUDES.map((a) => (
              <option key={a} value={a}>
                {a} M
              </option>
            ))}
          </select>
        </label>

        <label className="flex flex-col gap-1 font-mono text-[9px] uppercase tracking-widest text-text-secondary">
          <span>Region</span>
          <select
            defaultValue="donetsk"
            className="border border-border bg-surface-elevated px-2 py-1 font-mono text-[10px] text-text-primary"
          >
            <option value="donetsk">DONETSK</option>
          </select>
        </label>
      </div>
    </header>
  );
}
