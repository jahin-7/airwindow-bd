"use client";

import { createContext, useCallback, useContext, useEffect, useSyncExternalStore } from "react";

export type Lang = "en" | "bn";
export type Scale = "doe" | "epa" | "ugm3";

export interface Prefs {
  lang: Lang | null; // null until chosen on first open
  stationId: string;
  scale: Scale;
  pollutant: "pm25" | "pm10";
  alertsOn: boolean;
  alertThreshold: number; // µg/m³, PM2.5
  lowData: boolean;
  theme: "system" | "light" | "dark";
}

const DEFAULTS: Prefs = {
  lang: null,
  stationId: "dhk_darussalam",
  scale: "doe",
  pollutant: "pm25",
  alertsOn: false,
  alertThreshold: 55.5,
  lowData: false,
  theme: "system",
};
const KEY = "airwindow.prefs.v1";

function load(): Prefs {
  try {
    const raw = localStorage.getItem(KEY);
    return raw ? { ...DEFAULTS, ...JSON.parse(raw) } : DEFAULTS;
  } catch {
    return DEFAULTS;
  }
}

interface Ctx {
  prefs: Prefs;
  ready: boolean;
  set: (patch: Partial<Prefs>) => void;
  reset: () => void;
}

const PrefsCtx = createContext<Ctx | null>(null);

// Prefs live in localStorage; this tiny store lets React read them with useSyncExternalStore, so
// the first client render already has them (no effect that sets state and renders twice).
let current: Prefs | null = null;
const listeners = new Set<() => void>();
const snapshot = () => (current ??= load());
function write(next: Prefs) {
  current = next;
  try {
    localStorage.setItem(KEY, JSON.stringify(next));
  } catch {}
  listeners.forEach((l) => l());
}
function subscribe(l: () => void) {
  listeners.add(l);
  // another tab changed them
  const onStorage = (e: StorageEvent) => { if (e.key === KEY) { current = null; l(); } };
  window.addEventListener("storage", onStorage);
  return () => { listeners.delete(l); window.removeEventListener("storage", onStorage); };
}
const noop = () => () => {};

export function PrefsProvider({ children }: { children: React.ReactNode }) {
  const prefs = useSyncExternalStore(subscribe, snapshot, () => DEFAULTS);
  // false while rendering on the server and hydrating, true after
  const ready = useSyncExternalStore(noop, () => true, () => false);

  useEffect(() => {
    if (!ready) return;
    const root = document.documentElement;
    if (prefs.theme === "system") root.removeAttribute("data-theme");
    else root.setAttribute("data-theme", prefs.theme);
    root.lang = prefs.lang ?? "en";
  }, [prefs, ready]);

  const set = useCallback((patch: Partial<Prefs>) => write({ ...snapshot(), ...patch }), []);
  const reset = useCallback(() => {
    try {
      localStorage.removeItem(KEY);
    } catch {}
    current = DEFAULTS;
    listeners.forEach((l) => l());
  }, []);

  return <PrefsCtx.Provider value={{ prefs, ready, set, reset }}>{children}</PrefsCtx.Provider>;
}

export function usePrefs() {
  const c = useContext(PrefsCtx);
  if (!c) throw new Error("usePrefs outside PrefsProvider");
  return c;
}
