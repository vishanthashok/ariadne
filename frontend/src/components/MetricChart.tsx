"use client";

import {
  Area,
  AreaChart,
  CartesianGrid,
  Line,
  LineChart,
  ReferenceArea,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { MATCH_THRESHOLD } from "@/lib/constants";
import type { FrameResponse } from "@/lib/types";

export function ErrorChart({ history }: { history: FrameResponse[] }) {
  const data = history.map((f) => ({
    t: Number(f.timestamp.toFixed(1)),
    fused: f.metrics.error_m ?? 0,
    imu: f.metrics.imu_error_m ?? f.metrics.drift_m ?? 0,
    fix: f.metrics.visual_fix ? f.metrics.error_m : null,
  }));

  return (
    <div className="h-[200px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid stroke="#1e2130" strokeDasharray="3 3" />
          <XAxis
            dataKey="t"
            stroke="#3f3f46"
            tick={{ fill: "#71717a", fontSize: 10 }}
          />
          <YAxis
            stroke="#3f3f46"
            tick={{ fill: "#71717a", fontSize: 10 }}
            unit="m"
          />
          <Tooltip
            contentStyle={{
              background: "#0f1117",
              border: "1px solid #1e2130",
              fontSize: 11,
            }}
          />
          <ReferenceArea y1={0} y2={200} fill="#22c55e" fillOpacity={0.06} />
          <ReferenceArea y1={200} y2={500} fill="#f59e0b" fillOpacity={0.06} />
          <ReferenceArea y1={500} y2={5000} fill="#ef4444" fillOpacity={0.06} />
          <Line
            type="monotone"
            dataKey="fused"
            stroke="#3b82f6"
            dot={false}
            strokeWidth={1.5}
            name="Fused"
          />
          <Line
            type="monotone"
            dataKey="imu"
            stroke="#ef4444"
            strokeDasharray="4 4"
            dot={false}
            strokeWidth={1.2}
            name="IMU only"
          />
          <Line
            type="monotone"
            dataKey="fix"
            stroke="#22c55e"
            dot={{ r: 3, fill: "#22c55e" }}
            strokeWidth={0}
            name="Visual fix"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export function ConfidenceChart({ history }: { history: FrameResponse[] }) {
  const data = history.map((f) => ({
    t: Number(f.timestamp.toFixed(1)),
    conf: f.estimated_position.confidence,
  }));

  return (
    <div className="h-[150px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="confGrad" x1="0" y1="1" x2="0" y2="0">
              <stop offset="0%" stopColor="#3b82f6" stopOpacity={0.5} />
              <stop offset="100%" stopColor="#3b82f6" stopOpacity={0} />
            </linearGradient>
          </defs>
          <XAxis
            dataKey="t"
            stroke="#3f3f46"
            tick={{ fill: "#71717a", fontSize: 10 }}
          />
          <YAxis
            domain={[0, 1]}
            stroke="#3f3f46"
            tick={{ fill: "#71717a", fontSize: 10 }}
          />
          <ReferenceLine
            y={MATCH_THRESHOLD}
            stroke="#71717a"
            strokeDasharray="4 4"
            label={{
              value: "MATCH THRESHOLD",
              fill: "#71717a",
              fontSize: 9,
              position: "insideTopRight",
            }}
          />
          <Area
            type="monotone"
            dataKey="conf"
            stroke="#3b82f6"
            fill="url(#confGrad)"
            strokeWidth={1.5}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

export function MetricChart({ history }: { history: FrameResponse[] }) {
  return (
    <div className="space-y-3">
      <ErrorChart history={history} />
      <ConfidenceChart history={history} />
    </div>
  );
}
