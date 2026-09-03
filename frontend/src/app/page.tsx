"use client";

import { useState } from "react";
import { ControlBar } from "@/components/ControlBar";
import { DroneViewPanel } from "@/components/DroneViewPanel";
import { MapPanel } from "@/components/MapPanel";
import { TelemetryPanel } from "@/components/TelemetryPanel";
import { useSimulation } from "@/hooks/useSimulation";

type MobileTab = "drone" | "map" | "telemetry";

export default function HomePage() {
  const sim = useSimulation();
  const [tab, setTab] = useState<MobileTab>("map");

  return (
    <div className="grid h-screen grid-cols-1 grid-rows-[56px_1fr_48px] lg:grid-cols-[340px_1fr_380px] lg:grid-rows-[56px_minmax(0,1fr)]">
      <ControlBar
        playing={sim.playing}
        speed={sim.speed}
        isJammed={sim.isJammed}
        noise={sim.noise}
        altitude={sim.altitude}
        progress={sim.progress}
        demoMode={sim.demoMode}
        onPlay={sim.play}
        onPause={sim.pause}
        onSpeed={sim.setSpeed}
        onToggleJam={sim.toggleJamming}
        onNoise={sim.setNoise}
        onAltitude={sim.setAltitude}
        onRestart={sim.restart}
      />

      <div
        className={`min-h-0 ${tab === "drone" ? "block" : "hidden"} lg:block`}
      >
        <DroneViewPanel frame={sim.currentFrame} noise={sim.noise} />
      </div>
      <div className={`min-h-0 ${tab === "map" ? "block" : "hidden"} lg:block`}>
        <MapPanel
          frame={sim.currentFrame}
          history={sim.frameHistory}
          isJammed={sim.isJammed}
        />
      </div>
      <div
        className={`min-h-0 ${
          tab === "telemetry" ? "block" : "hidden"
        } lg:block`}
      >
        <TelemetryPanel frame={sim.currentFrame} history={sim.frameHistory} />
      </div>

      <nav className="flex border-t border-border bg-surface lg:hidden">
        {(
          [
            ["drone", "Drone"],
            ["map", "Map"],
            ["telemetry", "Telemetry"],
          ] as const
        ).map(([id, label]) => (
          <button
            key={id}
            type="button"
            onClick={() => setTab(id)}
            className={`flex-1 py-3 text-xs uppercase tracking-wider ${
              tab === id ? "text-estimated" : "text-text-secondary"
            }`}
          >
            {label}
          </button>
        ))}
      </nav>
    </div>
  );
}
