"use client";

interface Props {
  score: number;
  distanceKm: number;
  rank: number;
  label?: string;
}

export function MatchCard({ score, distanceKm, rank, label }: Props) {
  const pct = (score * 100).toFixed(1);
  let border = "border-error";
  if (score > 0.85) border = "border-confident";
  else if (score >= 0.6) border = "border-truth";
  const glow = rank === 0 ? "shadow-glow border-estimated" : border;

  return (
    <div
      className={`flex-1 min-w-0 rounded border ${glow} bg-surface-elevated p-2`}
    >
      <div className="mb-1.5 flex h-16 items-center justify-center rounded bg-background">
        <div
          className="h-full w-full rounded opacity-80"
          style={{
            background: `linear-gradient(135deg, #1e2130 0%, #3b82f633 50%, #161922 100%)`,
          }}
        />
      </div>
      <div className="font-mono text-[11px] text-text-primary">{pct}%</div>
      <div className="truncate text-[10px] text-text-secondary">
        {distanceKm.toFixed(2)} km
      </div>
      {label && (
        <div className="mt-0.5 truncate text-[9px] text-text-muted">{label}</div>
      )}
    </div>
  );
}

export function ConfidenceRing({ confidence }: { confidence: number }) {
  const r = 18;
  const c = 2 * Math.PI * r;
  const offset = c * (1 - Math.min(1, Math.max(0, confidence)));
  const color =
    confidence > 0.8 ? "#22c55e" : confidence > 0.5 ? "#f97316" : "#ef4444";
  return (
    <svg width="48" height="48" className="shrink-0">
      <circle cx="24" cy="24" r={r} stroke="#1e2130" strokeWidth="4" fill="none" />
      <circle
        cx="24"
        cy="24"
        r={r}
        stroke={color}
        strokeWidth="4"
        fill="none"
        strokeDasharray={c}
        strokeDashoffset={offset}
        strokeLinecap="round"
        transform="rotate(-90 24 24)"
      />
      <text
        x="24"
        y="28"
        textAnchor="middle"
        className="fill-text-primary"
        style={{ fontSize: 10, fontFamily: "JetBrains Mono" }}
      >
        {Math.round(confidence * 100)}
      </text>
    </svg>
  );
}
