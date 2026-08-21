"use client";

import { GitBranch, Pause, Play } from "lucide-react";
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
    <header className="col-span-full flex h-14 items-center gap-4 border-b border-border bg-surface px-4">
      <div className="flex min-w-[180px] items-center gap-2">
        <GitBranch className="h-4 w-4 text-estimated" />
        <div>
          <div className="text-sm font-semibold tracking-wide text-text-primary">
            ARIADNE
          </div>
          <div className="text-[10px] uppercase tracking-wider text-text-secondary">
            GPS-Denied Visual Navigation
          </div>
        </div>
        {props.demoMode && (
          <span className="ml-2 rounded border border-border px-1.5 py-0.5 text-[9px] uppercase text-text-secondary">
            Demo
          </span>
        )}
      </div>

      <div className="flex flex-1 items-center justify-center gap-3">
        <button
          type="button"
          onClick={props.playing ? props.onPause : props.onPlay}
          className="flex h-8 w-8 items-center justify-center rounded bg-surface-elevated text-text-primary shadow-glow"
          aria-label={props.playing ? "Pause" : "Play"}
        >
          {props.playing ? (
            <Pause className="h-4 w-4" />
          ) : (
            <Play className="h-4 w-4" />
          )}
        </button>
        <div className="flex overflow-hidden rounded border border-border">
          {SPEEDS.map((s) => (
            <button
              key={s}
              type="button"
              onClick={() => props.onSpeed(s)}
              className={`px-2.5 py-1 font-mono text-[11px] ${
                props.speed === s
                  ? "bg-estimated/20 text-estimated"
                  : "bg-surface-elevated text-text-secondary"
              }`}
            >
              {s}x
            </button>
          ))}
        </div>
        <div className="h-1 w-40 overflow-hidden rounded bg-border">
          <div
            className="h-full bg-estimated transition-all"
            style={{ width: `${Math.min(100, props.progress * 100)}%` }}
          />
        </div>
        <button
          type="button"
          onClick={props.onRestart}
          className="font-mono text-[10px] uppercase text-text-secondary hover:text-text-primary"
        >
          Restart
        </button>
      </div>

      <div className="flex items-center gap-4">
        <label className="flex items-center gap-2 text-[10px] uppercase text-text-secondary">
          GPS Jammed
          <button
            type="button"
            role="switch"
            aria-checked={props.isJammed}
            onClick={props.onToggleJam}
            className={`relative h-5 w-9 rounded-full transition ${
              props.isJammed
                ? "bg-error shadow-[0_0_12px_rgba(239,68,68,0.5)]"
                : "bg-confident shadow-[0_0_12px_rgba(34,197,94,0.5)]"
            }`}
          >
            <span
              className={`absolute top-0.5 h-4 w-4 rounded-full bg-white transition ${
                props.isJammed ? "left-4" : "left-0.5"
              }`}
            />
          </button>
        </label>

        <label className="flex w-28 flex-col gap-0.5 text-[10px] uppercase text-text-secondary">
          Camera Noise {Math.round(props.noise * 100)}%
          <input
            type="range"
            min={0}
            max={100}
            value={props.noise * 100}
            onChange={(e) => props.onNoise(Number(e.target.value) / 100)}
            className="h-1 accent-estimated"
          />
        </label>

        <label className="flex flex-col gap-0.5 text-[10px] uppercase text-text-secondary">
          Altitude
          <select
            value={props.altitude}
            onChange={(e) => props.onAltitude(Number(e.target.value))}
            className="rounded border border-border bg-surface-elevated px-2 py-1 font-mono text-[11px] text-text-primary"
          >
            {ALTITUDES.map((a) => (
              <option key={a} value={a}>
                {a}m
              </option>
            ))}
          </select>
        </label>

        <label className="flex flex-col gap-0.5 text-[10px] uppercase text-text-secondary">
          Region
          <select
            defaultValue="donetsk"
            className="rounded border border-border bg-surface-elevated px-2 py-1 font-mono text-[11px] text-text-primary"
          >
            <option value="donetsk">Donetsk</option>
          </select>
        </label>
      </div>
    </header>
  );
}
