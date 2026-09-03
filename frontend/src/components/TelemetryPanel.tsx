"use client";

import { AnimatePresence, motion } from "framer-motion";
import type { FrameResponse } from "@/lib/types";
import { ConfidenceRing } from "./MatchCard";
import { ConfidenceChart, ErrorChart } from "./MetricChart";

interface Props {
  frame: FrameResponse | null;
  history: FrameResponse[];
}

function DataRow({ label, value, accent }: { label: string; value: string; accent?: string }) {
  return (
    <div className="flex items-baseline justify-between border-b border-border/60 py-1 last:border-b-0">
      <span className="font-mono text-[9px] uppercase tracking-widest text-text-secondary">
        {label}
      </span>
      <span className={`font-mono text-[11px] ${accent ?? "text-text-primary"}`}>
        {value}
      </span>
    </div>
  );
}

export function TelemetryPanel({ frame, history }: Props) {
  const est = frame?.estimated_position;
  const conf = est?.confidence ?? 0;
  const visualWeight = Math.round(conf * 100);
  const imuWeight = 100 - visualWeight;
  const m = frame?.metrics;
  const err = m?.error_m ?? 0;
  const errColor =
    err < 200 ? "text-confident" : err < 500 ? "text-truth" : "text-error";
  const mode = frame?.mode ?? "VISUAL-INERTIAL";

  return (
    <aside className="flex h-full flex-col overflow-y-auto border-l border-border bg-surface">
      <div className="panel-header">
        <div className="flex items-center gap-2">
          <span className="status-dot bg-estimated" />
          <span className="panel-title">Navigation Telemetry</span>
        </div>
        <span className="font-mono text-[9px] tracking-widest text-text-muted">
          EKF · 6-DoF
        </span>
      </div>

      <div className="flex flex-col gap-3 p-3">
        <section className="border border-border bg-surface-elevated">
          <div className="flex items-center justify-between border-b border-border px-3 py-1.5">
            <span className="panel-title">Estimated Position</span>
            <span className={`font-mono text-[9px] uppercase tracking-widest ${errColor}`}>
              {mode}
            </span>
          </div>
          <div className="flex items-center gap-3 p-3">
            <ConfidenceRing confidence={conf} />
            <AnimatePresence mode="wait">
              <motion.div
                key={`${est?.lat?.toFixed(5)}-${est?.lon?.toFixed(5)}`}
                initial={{ opacity: 0.4, y: 4 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex-1 space-y-0.5 font-mono text-[12px] leading-tight text-text-primary"
              >
                <div className="flex gap-2">
                  <span className="w-8 text-text-muted">LAT</span>
                  <span>
                    {est
                      ? `${Math.abs(est.lat).toFixed(6)}°${est.lat >= 0 ? "N" : "S"}`
                      : "—"}
                  </span>
                </div>
                <div className="flex gap-2">
                  <span className="w-8 text-text-muted">LON</span>
                  <span>
                    {est
                      ? `${Math.abs(est.lon).toFixed(6)}°${est.lon >= 0 ? "E" : "W"}`
                      : "—"}
                  </span>
                </div>
                <div className="flex gap-2">
                  <span className="w-8 text-text-muted">σ</span>
                  <span>±{Math.round(est?.error_radius_m ?? 0)}m</span>
                </div>
              </motion.div>
            </AnimatePresence>
          </div>
          <div className="grid grid-cols-3 border-t border-border">
            <div className="px-3 py-1.5 text-center">
              <div className="font-mono text-[9px] uppercase tracking-widest text-text-secondary">
                ALT
              </div>
              <div className="font-mono text-[11px] text-text-primary">
                {Math.round(frame?.altitude_m ?? 200)}M
              </div>
            </div>
            <div className="border-l border-border px-3 py-1.5 text-center">
              <div className="font-mono text-[9px] uppercase tracking-widest text-text-secondary">
                HDG
              </div>
              <div className="font-mono text-[11px] text-text-primary">
                {Math.round(frame?.heading ?? 0).toString().padStart(3, "0")}°
              </div>
            </div>
            <div className="border-l border-border px-3 py-1.5 text-center">
              <div className="font-mono text-[9px] uppercase tracking-widest text-text-secondary">
                SPD
              </div>
              <div className="font-mono text-[11px] text-text-primary">
                {(frame?.speed_mps ?? 12).toFixed(1)}
              </div>
            </div>
          </div>
        </section>

        <section className="border border-border bg-surface-elevated">
          <div className="flex items-center justify-between border-b border-border px-3 py-1.5">
            <span className="panel-title">Position Error</span>
            <span className={`font-mono text-[11px] ${errColor}`}>
              {Math.round(err)}m
            </span>
          </div>
          <div className="p-1">
            <ErrorChart history={history} />
          </div>
        </section>

        <section className="border border-border bg-surface-elevated">
          <div className="flex items-center justify-between border-b border-border px-3 py-1.5">
            <span className="panel-title">Match Confidence</span>
            <span className="font-mono text-[11px] text-estimated">
              {(conf * 100).toFixed(0)}%
            </span>
          </div>
          <div className="p-1">
            <ConfidenceChart history={history} />
          </div>
        </section>

        <section className="border border-border bg-surface-elevated p-3">
          <div className="mb-2 flex items-center justify-between">
            <span className="panel-title">Sensor Fusion</span>
            <span className="font-mono text-[9px] tracking-widest text-text-muted">
              EKF WEIGHTS
            </span>
          </div>
          <div className="flex h-2 w-full overflow-hidden">
            <div
              className="bg-estimated transition-all"
              style={{ width: `${visualWeight}%` }}
            />
            <div
              className="bg-truth transition-all"
              style={{ width: `${imuWeight}%` }}
            />
          </div>
          <div className="mt-1.5 flex justify-between font-mono text-[10px]">
            <span className="text-estimated">◼ VISUAL {visualWeight}%</span>
            <span className="text-truth">◼ IMU {imuWeight}%</span>
          </div>
        </section>

        <section className="border border-border bg-surface-elevated">
          <div className="border-b border-border px-3 py-1.5">
            <span className="panel-title">Mission Metrics</span>
          </div>
          <div className="grid grid-cols-2 divide-x divide-y divide-border">
            {[
              ["Frames", `${m?.frames ?? history.length}`],
              ["Fixes", `${m?.fixes ?? 0}`],
              ["Avg Error", `${Math.round(m?.avg_error ?? 0)}m`],
              ["Max Drift", `${Math.round(m?.max_drift ?? 0)}m`],
              ["Fix Rate", `${Math.round((m?.fix_rate ?? 0) * 100)}%`],
              ["Runtime", `${(m?.runtime ?? 0).toFixed(0)}s`],
            ].map(([label, value]) => (
              <div key={String(label)} className="px-3 py-1.5">
                <div className="font-mono text-[9px] uppercase tracking-widest text-text-secondary">
                  {label}
                </div>
                <div className="font-mono text-[12px] text-text-primary">
                  {value}
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="border border-border bg-surface-elevated">
          <div className="border-b border-border px-3 py-1.5">
            <span className="panel-title">System Status</span>
          </div>
          <div className="px-3 py-2">
            <DataRow label="FAISS Index" value="READY" accent="text-confident" />
            <DataRow label="Siamese Net" value="ONLINE" accent="text-confident" />
            <DataRow label="EKF Filter" value="CONVERGED" accent="text-confident" />
            <DataRow
              label="GPS Signal"
              value={frame?.gps_jammed ? "JAMMED" : "NOMINAL"}
              accent={frame?.gps_jammed ? "text-error" : "text-confident"}
            />
          </div>
        </section>
      </div>
    </aside>
  );
}
