"use client";

interface Props {
  score: number;
  distanceKm: number;
  rank: number;
  label?: string;
}

export function MatchCard({ score, distanceKm, rank, label }: Props) {
  const pct = (score * 100).toFixed(1);
  let border = "border-error/60";
  let bar = "bg-error";
  if (score > 0.85) {
    border = "border-confident/60";
    bar = "bg-confident";
  } else if (score >= 0.6) {
    border = "border-truth/60";
    bar = "bg-truth";
  }
  const highlighted = rank === 0;
  const outer = highlighted
    ? "border-estimated/70 shadow-glow"
    : border;

  return (
    <div
      className={`flex-1 min-w-0 border ${outer} bg-surface-elevated p-1.5`}
    >
      <div className="mb-1.5 flex items-center justify-between">
        <span className="font-mono text-[9px] uppercase tracking-widest text-text-muted">
          #{rank + 1}
        </span>
        {highlighted && (
          <span className="font-mono text-[8px] uppercase tracking-widest text-estimated">
            LOCKED
          </span>
        )}
      </div>
      <div className="mb-1.5 flex h-14 items-center justify-center overflow-hidden bg-background">
        <div
          className="h-full w-full opacity-90"
          style={{
            background:
              rank === 0
                ? "linear-gradient(135deg, #1a2c4d 0%, #4c8dff44 50%, #0f1a2e 100%)"
                : rank === 1
                  ? "linear-gradient(135deg, #2a2418 0%, #f5a52444 50%, #1a1610 100%)"
                  : "linear-gradient(135deg, #1e2130 0%, #4c8dff22 50%, #10131a 100%)",
          }}
        />
      </div>
      <div className="mb-1 h-1 w-full bg-border">
        <div className={`h-full ${bar}`} style={{ width: `${pct}%` }} />
      </div>
      <div className="flex items-baseline justify-between">
        <span className="font-mono text-[11px] font-semibold text-text-primary">
          {pct}%
        </span>
        <span className="font-mono text-[9px] text-text-secondary">
          {distanceKm.toFixed(2)}KM
        </span>
      </div>
      {label && (
        <div className="mt-0.5 truncate font-mono text-[8px] uppercase tracking-widest text-text-muted">
          {label.split("/").pop()}
        </div>
      )}
    </div>
  );
}

export function ConfidenceRing({ confidence }: { confidence: number }) {
  const r = 18;
  const c = 2 * Math.PI * r;
  const offset = c * (1 - Math.min(1, Math.max(0, confidence)));
  const color =
    confidence > 0.8 ? "#3fb950" : confidence > 0.5 ? "#f0883e" : "#f04747";
  return (
    <svg width="48" height="48" className="shrink-0">
      <circle cx="24" cy="24" r={r} stroke="#1c2130" strokeWidth="3" fill="none" />
      <circle
        cx="24"
        cy="24"
        r={r}
        stroke={color}
        strokeWidth="3"
        fill="none"
        strokeDasharray={c}
        strokeDashoffset={offset}
        strokeLinecap="butt"
        transform="rotate(-90 24 24)"
      />
      <text
        x="24"
        y="28"
        textAnchor="middle"
        className="fill-text-primary"
        style={{ fontSize: 10, fontFamily: "JetBrains Mono", fontWeight: 600 }}
      >
        {Math.round(confidence * 100)}
      </text>
    </svg>
  );
}
