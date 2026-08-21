"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { FrameResponse } from "@/lib/types";
import { useWebSocket } from "./useWebSocket";

export function useSimulation() {
  const ws = useWebSocket();
  const [playing, setPlaying] = useState(true);
  const [speed, setSpeedState] = useState(1);
  const [isJammed, setIsJammed] = useState(true);
  const [noise, setNoiseState] = useState(0);
  const [altitude, setAltitudeState] = useState(200);
  const [demoMode, setDemoMode] = useState(false);
  const [progress, setProgress] = useState(0);
  const demoRef = useRef<FrameResponse[]>([]);
  const demoIdx = useRef(0);
  const rafRef = useRef<number | null>(null);
  const lastTick = useRef(0);

  // Fallback to demo JSON when WS fails
  useEffect(() => {
    if (!ws.failed || demoMode) return;
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch("/demo/simulation.json");
        if (!res.ok) throw new Error("demo missing");
        const data = (await res.json()) as FrameResponse[];
        if (cancelled) return;
        demoRef.current = data;
        setDemoMode(true);
        demoIdx.current = 0;
        ws.setFrameHistory([]);
      } catch {
        /* keep trying live */
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [ws.failed, demoMode, ws]);

  // Also try demo after short delay if never connected
  useEffect(() => {
    const t = setTimeout(async () => {
      if (ws.isConnected || demoMode) return;
      try {
        const res = await fetch("/demo/simulation.json");
        const data = (await res.json()) as FrameResponse[];
        demoRef.current = data;
        setDemoMode(true);
      } catch {
        /* ignore */
      }
    }, 2500);
    return () => clearTimeout(t);
  }, [ws.isConnected, demoMode]);

  useEffect(() => {
    if (!demoMode) return;
    const tick = (now: number) => {
      if (!playing) {
        rafRef.current = requestAnimationFrame(tick);
        return;
      }
      const interval = 500 / speed;
      if (now - lastTick.current >= interval) {
        lastTick.current = now;
        const frames = demoRef.current;
        if (frames.length) {
          let frame = { ...frames[demoIdx.current % frames.length] };
          frame = {
            ...frame,
            gps_jammed: isJammed,
            mode: isJammed
              ? frame.estimated_position.confidence > 0.3
                ? "VISUAL-INERTIAL"
                : "IMU ONLY"
              : "GPS",
            altitude_m: altitude,
          };
          if (!isJammed && frame.ground_truth) {
            frame.estimated_position = {
              ...frame.ground_truth,
              source: "gps",
              confidence: 1,
              error_radius_m: 5,
            };
            frame.metrics = {
              ...frame.metrics,
              error_m: 5 + Math.random() * 10,
            };
          }
          if (noise > 0) {
            frame = {
              ...frame,
              estimated_position: {
                ...frame.estimated_position,
                confidence: Math.max(
                  0.05,
                  frame.estimated_position.confidence * (1 - noise * 0.7)
                ),
              },
            };
          }
          ws.pushFrame(frame);
          demoIdx.current += 1;
          setProgress((demoIdx.current % frames.length) / frames.length);
        }
      }
      rafRef.current = requestAnimationFrame(tick);
    };
    rafRef.current = requestAnimationFrame(tick);
    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, [demoMode, playing, speed, isJammed, altitude, noise, ws]);

  const play = useCallback(() => {
    setPlaying(true);
    ws.sendControl("play");
  }, [ws]);

  const pause = useCallback(() => {
    setPlaying(false);
    ws.sendControl("pause");
  }, [ws]);

  const setSpeed = useCallback(
    (s: number) => {
      setSpeedState(s);
      ws.sendControl("set_speed", s);
    },
    [ws]
  );

  const toggleJamming = useCallback(() => {
    setIsJammed((j) => {
      const next = !j;
      ws.sendControl("toggle_jamming", next);
      return next;
    });
  }, [ws]);

  const setNoise = useCallback(
    (n: number) => {
      setNoiseState(n);
      ws.sendControl("set_noise", n);
    },
    [ws]
  );

  const setAltitude = useCallback(
    (a: number) => {
      setAltitudeState(a);
      ws.sendControl("set_altitude", a);
    },
    [ws]
  );

  const restart = useCallback(() => {
    demoIdx.current = 0;
    ws.setFrameHistory([]);
    ws.sendControl("restart");
    setPlaying(true);
  }, [ws]);

  const currentFrame = ws.currentFrame;
  const derived = useMemo(() => {
    const m = currentFrame?.metrics;
    return {
      currentError: m?.error_m ?? 0,
      totalDrift: m?.max_drift ?? 0,
      fixCount: m?.fixes ?? 0,
      frames: m?.frames ?? ws.frameHistory.length,
    };
  }, [currentFrame, ws.frameHistory.length]);

  return {
    ...derived,
    isConnected: ws.isConnected,
    demoMode,
    currentFrame,
    frameHistory: ws.frameHistory,
    playing,
    speed,
    isJammed,
    noise,
    altitude,
    progress: demoMode
      ? progress
      : currentFrame
        ? Math.min(1, (currentFrame.metrics.runtime ?? 0) / 500)
        : 0,
    play,
    pause,
    setSpeed,
    toggleJamming,
    setNoise,
    setAltitude,
    restart,
  };
}
