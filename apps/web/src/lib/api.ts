export type Pollutant = "pm25" | "pm10";

export interface Station {
  id: string;
  name: string;
  name_bn: string;
  city: string;
  lat: number;
  lon: number;
  distance_km?: number;
}

export interface Aqi24h {
  aqi: number;
  band: string;
  label_en: string;
  label_bn: string;
  color: string;
  mean_24h: number;
  hours_used: number;
  who_multiple: number;
  method: string;
}

export interface Reading {
  value: number;
  unit: string;
  observed_at: string;
  aqi_24h: Aqi24h | null;
  who_24h_guideline: number;
}

export interface Latest {
  station: Station;
  mode: "live" | "replay";
  status: "ok" | "stale" | "no_data";
  message?: string;
  observed_at?: string;
  age_hours?: number;
  source?: string;
  is_live?: boolean;
  provider_location?: string | null;
  provider_distance_m?: number | null;
  sensor_grade?: "reference" | "low_cost" | null;
  readings?: Partial<Record<Pollutant, Reading>>;
}

export interface Window {
  valid_at: string;
  horizon_h: number;
  value: number;
  lo80: number | null;
  hi80: number | null;
  kind: "measured" | "forecast";
  rank: number;
  relative_to_best_pct: number;
  clearly_lower_than_next: boolean;
}

export interface WindowsResponse {
  station_id: string;
  pollutant: Pollutant;
  issued_at: string;
  model_version: string;
  mode: "live" | "replay";
  is_live: boolean;
  windows: Window[];
  note: string;
}

export interface ForecastPoint {
  pollutant: Pollutant;
  horizon_h: number;
  valid_at: string;
  value: number;
  lo80: number;
  hi80: number;
  variant: string;
}

export interface ForecastResponse {
  issued_at: string;
  model_version: string;
  points: ForecastPoint[];
  reasons: string[];
  is_live: boolean;
  weather_source: string | null;
}

export interface Meta {
  mode: "live" | "replay";
  replay_note: string | null;
  stale_after_hours: number;
}

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

async function call<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(path, { ...init, headers: { "content-type": "application/json", ...init?.headers } });
  if (!r.ok) {
    let msg = r.statusText;
    try {
      msg = (await r.json()).detail ?? msg;
    } catch {}
    throw new ApiError(r.status, msg);
  }
  return r.json() as Promise<T>;
}

export const api = {
  meta: () => call<Meta>("/api/meta"),
  locations: (q = "") => call<Station[]>(`/api/locations?query=${encodeURIComponent(q)}`),
  nearby: (lat: number, lon: number) => call<Station[]>(`/api/stations/nearby?lat=${lat}&lon=${lon}`),
  latest: (id: string) => call<Latest>(`/api/observations/latest?station_id=${id}`),
  forecast: (id: string) => call<ForecastResponse>(`/api/forecast?station_id=${id}`),
  windows: (body: { station_id: string; pollutant: Pollutant; activity: string; duration_min: number }) =>
    call<WindowsResponse>("/api/activity-windows", { method: "POST", body: JSON.stringify(body) }),
  trends: (id: string, days: number) =>
    call<{ daily: { date: string; pm25_mean: number | null; pm10_mean: number | null }[]; hourly: { ts: string; pm25: number | null; pm10: number | null }[]; source: string }>(
      `/api/trends?station_id=${id}&days=${days}`),
  modelCard: () => call<Record<string, unknown>>("/api/model-card"),
};
