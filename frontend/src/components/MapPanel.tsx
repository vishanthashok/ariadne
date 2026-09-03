"use client";

import { Crosshair } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";
import { DEFAULT_CENTER, MAPBOX_TOKEN } from "@/lib/constants";
import { hasMapboxToken } from "@/lib/mapbox";
import type { FrameResponse } from "@/lib/types";

interface Props {
  frame: FrameResponse | null;
  history: FrameResponse[];
  isJammed: boolean;
}

export function MapPanel({ frame, history, isJammed }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<mapboxgl.Map | null>(null);
  const markerRef = useRef<mapboxgl.Marker | null>(null);
  const followRef = useRef(true);
  const [ready, setReady] = useState(false);
  const tokenOk = hasMapboxToken();

  useEffect(() => {
    if (!tokenOk || !containerRef.current || mapRef.current) return;
    mapboxgl.accessToken = MAPBOX_TOKEN;
    const map = new mapboxgl.Map({
      container: containerRef.current,
      style: "mapbox://styles/mapbox/satellite-streets-v12",
      center: DEFAULT_CENTER,
      zoom: 11,
      attributionControl: false,
    });
    mapRef.current = map;
    map.on("load", () => {
      map.addSource("est-path", {
        type: "geojson",
        data: {
          type: "Feature",
          properties: {},
          geometry: { type: "LineString", coordinates: [] },
        },
      });
      map.addSource("truth-path", {
        type: "geojson",
        data: {
          type: "Feature",
          properties: {},
          geometry: { type: "LineString", coordinates: [] },
        },
      });
      map.addSource("confidence", {
        type: "geojson",
        data: {
          type: "Feature",
          properties: {},
          geometry: { type: "Polygon", coordinates: [] },
        },
      });
      map.addSource("match-line", {
        type: "geojson",
        data: {
          type: "Feature",
          properties: {},
          geometry: { type: "LineString", coordinates: [] },
        },
      });
      map.addSource("jam-zone", {
        type: "geojson",
        data: {
          type: "Feature",
          properties: {},
          geometry: {
            type: "Polygon",
            coordinates: [
              [
                [37.5, 48.0],
                [38.5, 48.0],
                [38.5, 48.8],
                [37.5, 48.8],
                [37.5, 48.0],
              ],
            ],
          },
        },
      });

      map.addLayer({
        id: "est-glow",
        type: "line",
        source: "est-path",
        paint: { "line-color": "#3b82f6", "line-width": 8, "line-opacity": 0.25 },
      });
      map.addLayer({
        id: "est-line",
        type: "line",
        source: "est-path",
        paint: { "line-color": "#3b82f6", "line-width": 2.5 },
      });
      map.addLayer({
        id: "truth-line",
        type: "line",
        source: "truth-path",
        paint: {
          "line-color": "#f59e0b",
          "line-width": 2,
          "line-opacity": 0.7,
          "line-dasharray": [2, 2],
        },
      });
      map.addLayer({
        id: "conf-fill",
        type: "fill",
        source: "confidence",
        paint: { "fill-color": "#3b82f6", "fill-opacity": 0.1 },
      });
      map.addLayer({
        id: "conf-stroke",
        type: "line",
        source: "confidence",
        paint: { "line-color": "#3b82f6", "line-opacity": 0.3, "line-width": 1 },
      });
      map.addLayer({
        id: "match-line",
        type: "line",
        source: "match-line",
        paint: {
          "line-color": "#ffffff",
          "line-width": 1,
          "line-dasharray": [2, 2],
          "line-opacity": 0.6,
        },
      });
      map.addLayer({
        id: "jam-fill",
        type: "fill",
        source: "jam-zone",
        paint: { "fill-color": "#ef4444", "fill-opacity": isJammed ? 0.12 : 0 },
      });

      const el = document.createElement("div");
      el.className = "ariadne-marker";
      el.innerHTML =
        '<div class="pulse-ring"></div><div class="pulse-dot"></div>';
      markerRef.current = new mapboxgl.Marker(el)
        .setLngLat(DEFAULT_CENTER)
        .addTo(map);
      setReady(true);
    });

    map.on("dragstart", () => {
      followRef.current = false;
    });

    return () => {
      map.remove();
      mapRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tokenOk]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready || !frame) return;

    const estCoords = history.map((f) => [
      f.estimated_position.lon,
      f.estimated_position.lat,
    ]);
    const truthCoords = history
      .filter((f) => f.ground_truth)
      .map((f) => [f.ground_truth!.lon, f.ground_truth!.lat]);

    (map.getSource("est-path") as mapboxgl.GeoJSONSource)?.setData({
      type: "Feature",
      properties: {},
      geometry: { type: "LineString", coordinates: estCoords },
    });
    (map.getSource("truth-path") as mapboxgl.GeoJSONSource)?.setData({
      type: "Feature",
      properties: {},
      geometry: { type: "LineString", coordinates: truthCoords },
    });

    const lon = frame.estimated_position.lon;
    const lat = frame.estimated_position.lat;
    markerRef.current?.setLngLat([lon, lat]);

    const radiusM = frame.estimated_position.error_radius_m || 100;
    const dLat = radiusM / 111_320;
    const dLon = radiusM / (111_320 * Math.cos((lat * Math.PI) / 180));
    const ring: [number, number][] = [];
    for (let i = 0; i <= 64; i++) {
      const a = (i / 64) * Math.PI * 2;
      ring.push([lon + dLon * Math.cos(a), lat + dLat * Math.sin(a)]);
    }
    (map.getSource("confidence") as mapboxgl.GeoJSONSource)?.setData({
      type: "Feature",
      properties: {},
      geometry: { type: "Polygon", coordinates: [ring] },
    });

    if (frame.top_matches?.[0]) {
      (map.getSource("match-line") as mapboxgl.GeoJSONSource)?.setData({
        type: "Feature",
        properties: {},
        geometry: {
          type: "LineString",
          coordinates: [
            [lon, lat],
            [frame.top_matches[0].lon, frame.top_matches[0].lat],
          ],
        },
      });
    }

    if (map.getLayer("jam-fill")) {
      map.setPaintProperty("jam-fill", "fill-opacity", isJammed ? 0.12 : 0);
    }

    if (followRef.current) {
      const zoom = Math.max(9, 14 - frame.altitude_m / 200);
      map.flyTo({ center: [lon, lat], zoom, duration: 1000 });
    }
  }, [frame, history, ready, isJammed]);

  const err = frame?.metrics.error_m ?? 0;
  const errColor =
    err < 200 ? "text-confident" : err < 500 ? "text-truth" : "text-error";

  return (
    <section className="relative h-full bg-background">
      {tokenOk ? (
        <div ref={containerRef} className="h-full w-full" />
      ) : (
        <div className="flex h-full flex-col items-center justify-center gap-3 bg-[radial-gradient(ellipse_at_center,#0f1a2e,#06060a)] p-8 text-center">
          <div className="font-mono text-sm text-estimated">MAP VIEW</div>
          <p className="max-w-md text-sm text-text-secondary">
            Set{" "}
            <code className="text-text-primary">
              NEXT_PUBLIC_MAPBOX_ACCESS_TOKEN
            </code>{" "}
            in{" "}
            <code className="text-text-primary">frontend/.env.local</code> to
            enable satellite basemap. Trajectory telemetry still updates below.
          </p>
          {frame && (
            <div className="font-mono text-xs text-text-primary">
              EST {frame.estimated_position.lat.toFixed(5)}°N{" "}
              {frame.estimated_position.lon.toFixed(5)}°E
            </div>
          )}
          {isJammed && (
            <div className="mt-2 border border-error/40 bg-error/10 px-3 py-1 font-mono text-[11px] text-error">
              EW ACTIVE
            </div>
          )}
        </div>
      )}

      <div className="pointer-events-none absolute left-3 top-3 z-10 flex items-center gap-2 border border-border bg-surface/85 px-2.5 py-1 backdrop-blur-md">
        <span className="status-dot bg-estimated" />
        <span className="panel-title">Tactical Map · Donetsk Oblast</span>
        <span className="ml-2 font-mono text-[9px] tracking-widest text-text-muted">
          WGS-84 · EPSG:4326
        </span>
      </div>

      <div className="pointer-events-none absolute right-3 top-3 z-10 flex flex-col gap-1 border border-border bg-surface/85 px-2.5 py-1.5 font-mono text-[10px] backdrop-blur-md">
        <div className="flex items-center gap-2">
          <span className="h-0.5 w-4 bg-estimated" />
          <span className="text-text-secondary">EST · VISUAL-INERTIAL</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="h-0.5 w-4 border-t border-dashed border-truth" />
          <span className="text-text-secondary">TRUTH · GROUND</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="h-2 w-4 border border-estimated/50 bg-estimated/10" />
          <span className="text-text-secondary">CONFIDENCE ELLIPSE</span>
        </div>
      </div>

      <button
        type="button"
        className="absolute bottom-16 right-3 z-10 flex h-9 w-9 items-center justify-center border border-border bg-surface/90 text-text-primary backdrop-blur-md hover:border-estimated"
        onClick={() => {
          followRef.current = true;
          if (frame && mapRef.current) {
            mapRef.current.flyTo({
              center: [
                frame.estimated_position.lon,
                frame.estimated_position.lat,
              ],
              duration: 800,
            });
          }
        }}
        aria-label="Recenter"
      >
        <Crosshair className="h-4 w-4" />
      </button>

      <div className="absolute bottom-3 left-3 right-3 z-10 grid grid-cols-4 items-center gap-4 border border-border bg-surface/85 px-4 py-2 backdrop-blur-md">
        <div>
          <div className="font-mono text-[9px] uppercase tracking-widest text-text-secondary">
            Position Error
          </div>
          <div className={`font-mono text-lg font-semibold leading-tight ${errColor}`}>
            {Math.round(err)}<span className="text-xs text-text-muted"> M</span>
          </div>
        </div>
        <div>
          <div className="font-mono text-[9px] uppercase tracking-widest text-text-secondary">
            Mode
          </div>
          <div className="font-mono text-sm text-text-primary">
            {frame?.mode ?? "VISUAL-INERTIAL"}
          </div>
        </div>
        <div>
          <div className="font-mono text-[9px] uppercase tracking-widest text-text-secondary">
            Runtime
          </div>
          <div className="font-mono text-sm text-text-primary">
            T+{(frame?.timestamp ?? 0).toFixed(1)}S
          </div>
        </div>
        <div className="text-right">
          <div className="font-mono text-[9px] uppercase tracking-widest text-text-secondary">
            Status
          </div>
          <div className="font-mono text-sm text-confident">
            <span className="status-dot bg-confident" />
            TRACKING
          </div>
        </div>
      </div>
    </section>
  );
}
