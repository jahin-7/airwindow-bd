"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";

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

export function PrefsProvider({ children }: { children: React.ReactNode }) {
  const [prefs, setPrefs] = useState<Prefs>(DEFAULTS);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    // Reading localStorage must wait for the client.
    setPrefs(load());
    setReady(true);
  }, []);

  useEffect(() => {
    if (!ready) return;
    try {
      localStorage.setItem(KEY, JSON.stringify(prefs));
    } catch {}
    const root = document.documentElement;
    if (prefs.theme === "system") root.removeAttribute("data-theme");
    else root.setAttribute("data-theme", prefs.theme);
    root.lang = prefs.lang ?? "en";
  }, [prefs, ready]);

  const set = useCallback((patch: Partial<Prefs>) => setPrefs((p) => ({ ...p, ...patch })), []);
  const reset = useCallback(() => {
    try {
      localStorage.removeItem(KEY);
    } catch {}
    setPrefs(DEFAULTS);
  }, []);

  return <PrefsCtx.Provider value={{ prefs, ready, set, reset }}>{children}</PrefsCtx.Provider>;
}

export function usePrefs() {
  const c = useContext(PrefsCtx);
  if (!c) throw new Error("usePrefs outside PrefsProvider");
  return c;
}
