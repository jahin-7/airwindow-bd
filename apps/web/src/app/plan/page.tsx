"use client";

import { useEffect, useState } from "react";
import { ReplayBanner } from "@/components/AppShell";
import { Card, KindTag, LargeTitle, SectionLabel, Segmented, Skeleton } from "@/components/ui";
import { api, ApiError, type WindowsResponse } from "@/lib/api";
import { clock, dict, num } from "@/lib/i18n";
import { usePrefs } from "@/lib/prefs";

const ACTS = ["walk", "exercise", "commute", "school_run", "errands"] as const;

export default function Plan() {
  const { prefs, set } = usePrefs();
  const t = dict(prefs.lang);
  const [act, setAct] = useState<(typeof ACTS)[number]>("walk");
  const [res, setRes] = useState<WindowsResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    let live = true;
    api.windows({ station_id: prefs.stationId, pollutant: prefs.pollutant, activity: act, duration_min: 60 })
      .then((r) => { if (live) { setRes(r); setErr(null); } })
      .catch((e) => { if (live) { setRes(null); setErr(e instanceof ApiError ? e.message : t.errorGeneric); } });
    return () => { live = false; };
  }, [prefs.stationId, prefs.pollutant, act, t.errorGeneric]);

  return (
    <>
      <LargeTitle title={t.planTitle} sub={t.tagline} />
      <ReplayBanner />
      <div className="space-y-3 px-4">
        <Card>
          <div className="text-[13px] font-medium text-ink-3">{t.activity}</div>
          <div className="mt-3 flex flex-wrap gap-2">
            {ACTS.map((a) => (
              <button key={a} onClick={() => setAct(a)} aria-pressed={act === a}
                className={`rounded-full px-4 py-2 text-[14px] font-medium transition-colors ${act === a ? "bg-accent-fill text-white" : "bg-card-2"}`}>
                {t.acts[a]}
              </button>
            ))}
          </div>
          <div className="mt-5 text-[13px] font-medium text-ink-3">{t.pollutant}</div>
          <div className="mt-3">
            <Segmented label="pollutant" value={prefs.pollutant} onChange={(v) => set({ pollutant: v })}
              options={[{ value: "pm25", label: "PM2.5" }, { value: "pm10", label: "PM10" }]} />
          </div>
        </Card>

        <SectionLabel>{t.rankedHours}</SectionLabel>
        {!res && !err && <Skeleton className="h-56" />}
        {err && <Card tone="warn"><p className="text-[14px]">{err}</p></Card>}
        {res && (
          <Card className="divide-y divide-line !py-1">
            {res.windows.map((w) => (
              <div key={w.valid_at} className="flex items-center gap-4 py-4">
                <span className={`grid h-9 w-9 shrink-0 place-items-center rounded-full text-[15px] font-semibold ${w.rank === 1 ? "bg-accent-fill text-white" : "bg-card-2"}`}>
                  {num(prefs.lang, w.rank)}
                </span>
                <div className="min-w-0 flex-1">
                  <div className="text-[17px] font-semibold">
                    {w.horizon_h === 0 ? (prefs.lang === "bn" ? "এখন" : "Now") : clock(prefs.lang, w.valid_at)}
                    {w.horizon_h > 0 && <span className="ml-2 text-[13px] font-normal text-ink-2">{t.inHours(w.horizon_h)}</span>}
                  </div>
                  <div className="mt-1"><KindTag kind={w.kind} label={w.kind === "measured" ? t.measured : t.forecast} /></div>
                  {w.rank === 1 && res.windows.length > 1 && (
                    <div className="mt-1 text-[12px] text-ink-3">{w.clearly_lower_than_next ? t.clearlyLower : t.overlap}</div>
                  )}
                </div>
                <div className="text-right">
                  <div className="tabular text-[20px] font-semibold">{num(prefs.lang, w.value)}</div>
                  <div className="tabular text-[12px] text-ink-3">
                    {w.lo80 != null && w.hi80 != null ? `${num(prefs.lang, w.lo80)}–${num(prefs.lang, w.hi80)}` : "µg/m³"}
                  </div>
                </div>
              </div>
            ))}
          </Card>
        )}
        {res && <p className="px-2 text-[12px] leading-relaxed text-ink-3">{t.notSafety} · model {res.model_version}</p>}
      </div>
    </>
  );
}
