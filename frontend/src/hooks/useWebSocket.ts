"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { HISTORY_LIMIT, WS_URL } from "@/lib/constants";
import type { FrameResponse } from "@/lib/types";

export function useWebSocket() {
  const [isConnected, setIsConnected] = useState(false);
  const [currentFrame, setCurrentFrame] = useState<FrameResponse | null>(null);
  const [frameHistory, setFrameHistory] = useState<FrameResponse[]>([]);
  const [failed, setFailed] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const backoffRef = useRef(500);
  const aliveRef = useRef(true);

  const pushFrame = useCallback((frame: FrameResponse) => {
    setCurrentFrame(frame);
    setFrameHistory((prev) => {
      const next = [...prev, frame];
      return next.length > HISTORY_LIMIT ? next.slice(-HISTORY_LIMIT) : next;
    });
  }, []);

  const connect = useCallback(() => {
    if (!aliveRef.current) return;
    try {
      const ws = new WebSocket(`${WS_URL}/ws/simulate`);
      wsRef.current = ws;
      ws.onopen = () => {
        setIsConnected(true);
        setFailed(false);
        backoffRef.current = 500;
      };
      ws.onmessage = (ev) => {
        try {
          const msg = JSON.parse(ev.data);
          if (msg.type === "frame" && msg.data) {
            pushFrame(msg.data as FrameResponse);
          }
        } catch {
          /* ignore */
        }
      };
      ws.onclose = () => {
        setIsConnected(false);
        wsRef.current = null;
        const delay = backoffRef.current;
        backoffRef.current = Math.min(delay * 2, 8000);
        if (backoffRef.current >= 8000) setFailed(true);
        setTimeout(connect, delay);
      };
      ws.onerror = () => {
        ws.close();
      };
    } catch {
      setFailed(true);
    }
  }, [pushFrame]);

  useEffect(() => {
    aliveRef.current = true;
    connect();
    return () => {
      aliveRef.current = false;
      wsRef.current?.close();
    };
  }, [connect]);

  const sendControl = useCallback((action: string, value?: unknown) => {
    const payload = JSON.stringify({ action, value });
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(payload);
    }
  }, []);

  return {
    isConnected,
    currentFrame,
    frameHistory,
    sendControl,
    failed,
    setCurrentFrame,
    setFrameHistory,
    pushFrame,
  };
}
