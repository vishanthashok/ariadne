import mapboxgl from "mapbox-gl";
import { MAPBOX_TOKEN } from "./constants";

export function initMapbox(): typeof mapboxgl {
  mapboxgl.accessToken = MAPBOX_TOKEN;
  return mapboxgl;
}

export function hasMapboxToken(): boolean {
  return Boolean(MAPBOX_TOKEN && MAPBOX_TOKEN.length > 10);
}
