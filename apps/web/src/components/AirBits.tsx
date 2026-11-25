"use client";

import { motion } from "motion/react";
import type { Reading, Window } from "@/lib/api";
import { clock, dict, num } from "@/lib/i18n";
import { usePrefs } from "@/lib/prefs";
import { KindTag } from "./ui";

/** AQI band per the chosen number style. DoE bands and EPA index share breakpoints (see Methodology). */
export function AqiChip({ r }: { r: Reading }) {
  const { prefs } = usePrefs();
  const t = dict(prefs.lang);
  if (prefs.scale === "ugm3") return null;
  if (!r.aqi_24h) return <div className="mt-3 text-[13px] text-ink-3">{t.aqiNeeds}</div>;
  const a = r.aqi_24h;
  const label = prefs.lang === "bn" ? a.label_bn : a.label_en;
  return (
    <div className="mt-4 flex items-center gap-3">
      <span className="h-9 w-2 rounded-full ring-1 ring-ink/25" style={{ background: a.color }} aria-hidden />
      <div>
        <div className="text-[15px] font-semibold">
          {prefs.scale === "doe" ? "AQI" : "US AQI"} {num(prefs.lang, a.aqi)} · {label}
        </div>
        <div className="text-[13px] text-ink-2">
          {prefs.lang === "bn" ? `২৪ ঘণ্টার গড় ${num(prefs.lang, a.mean_24h)} µg/m³` : `24-hour average ${num(prefs.lang, a.mean_24h)} µg/m³`}
        </div>
        <div className="text-[13px] text-ink-2">{t.whoMultiple(a.who_multiple)}</div>
      </div>
    </div>
  );
}

/** Now + forecast hours as bars on one scale. Forecast bars show the 80% range. */
export function HoursStrip({ windows }: { windows: Window[] }) {
  const { prefs } = usePrefs();
  const t = dict(prefs.lang);
  const pts = [...windows].sort((a, b) => a.horizon_h - b.horizon_h);
  const max = Math.max(...pts.map((p) => p.hi80 ?? p.value)) * 1.08 || 1;
  const best = pts.find((p) => p.rank === 1);
  return (
    <div className="flex h-48 items-end gap-3 pt-6" role="list">
      {pts.map((p, i) => {
        const isBest = p === best;
        const h = (p.value / max) * 100;
        return (
          <div key={p.valid_at} role="listitem" className="flex h-full flex-1 flex-col items-center justify-end gap-2"
            aria-label={`${clock(prefs.lang, p.valid_at)}: ${p.value} µg/m³ ${p.kind === "measured" ? t.measured : t.forecast}`}>
            <div className="relative w-full max-w-[56px] flex-1">
              <span className={`tabular absolute inset-x-0 text-center text-[13px] font-semibold ${isBest ? "text-accent" : ""}`}
                style={{ bottom: `calc(${Math.max(h, (p.hi80 ?? 0) / max * 100)}% + 6px)` }}>{num(prefs.lang, p.value)}</span>
              {p.lo80 != null && p.hi80 != null && (
                <div className="absolute inset-x-[30%] rounded-full bg-accent/15"
                  style={{ bottom: `${(p.lo80 / max) * 100}%`, height: `${((p.hi80 - p.lo80) / max) * 100}%` }} aria-hidden />
              )}
              <motion.div initial={{ height: 0 }} animate={{ height: `${h}%` }}
                transition={{ type: "spring", stiffness: 220, damping: 26, delay: i * 0.05 }}
                className={`absolute inset-x-0 bottom-0 rounded-[14px] ${p.kind === "measured" ? "bg-ink" : isBest ? "bg-accent" : "border-2 border-dashed border-forecast bg-transparent"}`} />
            </div>
            <span className="text-[12px] text-ink-2">{p.horizon_h === 0 ? (prefs.lang === "bn" ? "এখন" : "Now") : clock(prefs.lang, p.valid_at)}</span>
          </div>
        );
      })}
    </div>
  );
}

export function Legend() {
  const { prefs } = usePrefs();
  const t = dict(prefs.lang);
  return (
    <div className="mt-4 flex flex-wrap gap-4">
      <KindTag kind="measured" label={t.measured} />
      <KindTag kind="forecast" label={t.forecast} />
      <span className="inline-flex items-center gap-1.5 text-[12px] text-ink-2">
        <span className="h-3 w-2 rounded-full bg-accent/15" aria-hidden /> {t.forecastRange} (80%)
      </span>
    </div>
  );
}
