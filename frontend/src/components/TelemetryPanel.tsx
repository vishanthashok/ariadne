"use client";

import { AnimatePresence, motion } from "framer-motion";
import type { FrameResponse } from "@/lib/types";
import { ConfidenceRing } from "./MatchCard";
import { ConfidenceChart, ErrorChart } from "./MetricChart";

interface Props {
  frame: FrameResponse | null;
  history: FrameResponse[];
}

export function TelemetryPanel({ frame, history }: Props) {
  const est = frame?.estimated_position;
  const conf = est?.confidence ?? 0;
  const visualWeight = Math.round(conf * 100);
  const imuWeight = 100 - visualWeight;
  const m = frame?.metrics;

  return (
    <aside className="flex h-full flex-col gap-3 overflow-y-auto border-l border-border bg-surface p-3">
      <section className="rounded border border-border bg-surface-elevated p-3">
        <div className="mb-2 flex items-center justify-between">
          <div className="text-[11px] uppercase tracking-wider text-text-secondary">
            Estimated Position
          </div>
          <ConfidenceRing confidence={conf} />
        </div>
        <AnimatePresence mode="wait">
          <motion.div
            key={`${est?.lat?.toFixed(5)}-${est?.lon?.toFixed(5)}`}
            initial={{ opacity: 0.4, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-1 font-mono text-sm text-text-primary"
          >
            <div>
              LAT{" "}
              {est
                ? `${Math.abs(est.lat).toFixed(6)}°${est.lat >= 0 ? "N" : "S"}`
                : "—"}
            </div>
            <div>
              LON{" "}
              {est
                ? `${Math.abs(est.lon).toFixed(6)}°${est.lon >= 0 ? "E" : "W"}`
                : "—"}
            </div>
            <div className="pt-1 text-[12px] text-text-secondary">
              ALT {Math.round(frame?.altitude_m ?? 200)}m | HDG{" "}
              {Math.round(frame?.heading ?? 0).toString().padStart(3, "0")}° |
              SPD {(frame?.speed_mps ?? 12).toFixed(0)} m/s
            </div>
          </motion.div>
        </AnimatePresence>
      </section>

      <section>
        <div className="mb-1 text-[11px] uppercase tracking-wider text-text-secondary">
          Position Error
        </div>
        <ErrorChart history={history} />
      </section>

      <section>
        <div className="mb-1 text-[11px] uppercase tracking-wider text-text-secondary">
          Match Confidence
        </div>
        <ConfidenceChart history={history} />
      </section>

      <section className="rounded border border-border bg-surface-elevated p-3">
        <div className="mb-2 text-[11px] uppercase tracking-wider text-text-secondary">
          Sensor Fusion
        </div>
        <div className="flex h-3 w-full overflow-hidden rounded">
          <div
            className="bg-estimated transition-all"
            style={{ width: `${visualWeight}%` }}
            title={`VISUAL ${visualWeight}%`}
          />
          <div
            className="bg-truth transition-all"
            style={{ width: `${imuWeight}%` }}
            title={`IMU ${imuWeight}%`}
          />
        </div>
        <div className="mt-1 flex justify-between font-mono text-[10px] text-text-secondary">
          <span>VISUAL {visualWeight}%</span>
          <span>IMU {imuWeight}%</span>
        </div>
      </section>

      <section className="grid grid-cols-2 gap-2">
        {[
          ["FRAMES", m?.frames ?? history.length],
          ["FIXES", m?.fixes ?? 0],
          ["AVG ERROR", `${Math.round(m?.avg_error ?? 0)}m`],
          ["MAX DRIFT", `${Math.round(m?.max_drift ?? 0)}m`],
          ["FIX RATE", `${Math.round((m?.fix_rate ?? 0) * 100)}%`],
          ["RUNTIME", `${(m?.runtime ?? 0).toFixed(0)}s`],
        ].map(([label, value]) => (
          <div
            key={String(label)}
            className="rounded border border-border bg-surface-elevated px-2 py-2"
          >
            <div className="text-[9px] uppercase tracking-wider text-text-secondary">
              {label}
            </div>
            <div className="font-mono text-sm text-text-primary">{value}</div>
          </div>
        ))}
      </section>
    </aside>
  );
}
