"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { AqiChip, HoursStrip, Legend } from "@/components/AirBits";
import { ReplayBanner } from "@/components/AppShell";
import { Card, KindTag, LargeTitle, SectionLabel, Skeleton } from "@/components/ui";
import { api, ApiError, type Latest, type WindowsResponse } from "@/lib/api";
import { clock, dict, num } from "@/lib/i18n";
import { usePrefs } from "@/lib/prefs";

export default function Today() {
  const { prefs } = usePrefs();
  const t = dict(prefs.lang);
  const [latest, setLatest] = useState<Latest | null>(null);
  const [win, setWin] = useState<WindowsResponse | null>(null);
  const [winErr, setWinErr] = useState<string | null>(null);
  const [err, setErr] = useState(false);

  const load = useCallback(() => {
    setErr(false);
    api.latest(prefs.stationId).then(setLatest).catch(() => setErr(true));
    api.windows({ station_id: prefs.stationId, pollutant: prefs.pollutant, activity: "walk", duration_min: 60 })
      .then((w) => { setWin(w); setWinErr(null); })
      .catch((e) => { setWin(null); setWinErr(e instanceof ApiError ? e.message : t.errorGeneric); });
  }, [prefs.stationId, prefs.pollutant, t.errorGeneric]);

  useEffect(() => { load(); }, [load]);

  const name = latest ? (prefs.lang === "bn" ? latest.station.name_bn : latest.station.name) : "";
  const best = win?.windows.find((w) => w.rank === 1);
  const title = !win ? (winErr ? t.noWindow : t.loading)
    : best?.horizon_h === 0 ? t.bestNow
    : best ? `${clock(prefs.lang, best.valid_at)} · ${t.inHours(best.horizon_h)}` : t.noWindow;
  const reading = latest?.readings?.[prefs.pollutant];

  return (
    <>
      <LargeTitle title={title} sub={
        <Link href="/stations" className="inline-flex items-center gap-2 rounded-full bg-card px-3 py-1.5 text-[14px] text-ink">
          <span className="text-accent">●</span> {t.bestWindow} · {name || "…"} <span aria-hidden>›</span>
        </Link>} />
      <ReplayBanner />
      <div className="space-y-3 px-4 lg:grid lg:grid-cols-2 lg:items-start lg:gap-4 lg:space-y-0">
        {err && (
          <Card tone="warn" className="lg:col-span-2"><p>{t.errorGeneric}</p>
            <button onClick={load} className="mt-3 rounded-full bg-accent-fill px-4 py-2 text-white">{t.retry}</button></Card>
        )}
        {!latest && !err && <Skeleton className="h-44" />}

        {latest?.status === "no_data" && (
          <Card tone="warn" className="lg:col-span-2"><div className="font-semibold">{t.noData}</div><p className="mt-1 text-[14px] text-ink-2">{t.noDataSub}</p></Card>
        )}
        {latest?.status === "stale" && (
          <Card tone="warn" className="lg:col-span-2"><div className="font-semibold">{t.stale}</div><p className="mt-1 text-[14px] text-ink-2">{t.staleSub(latest.age_hours ?? 0)}</p></Card>
        )}

        {reading && latest && (
          <Card>
            <div className="flex items-center justify-between">
              <KindTag kind="measured" label={`${t.measured} · ${prefs.pollutant === "pm25" ? "PM2.5" : "PM10"}`} />
              <span className="text-[12px] text-ink-3">{clock(prefs.lang, reading.observed_at)}</span>
            </div>
            <div className="mt-2 flex items-baseline gap-2">
              <span className="tabular text-[64px] font-semibold leading-none tracking-tight">{num(prefs.lang, reading.value)}</span>
              <span className="text-[17px] text-ink-2">µg/m³</span>
            </div>
            <AqiChip r={reading} />
            <div className="mt-4 border-t border-line pt-3 text-[12px] text-ink-3">
              {t.source}: {latest.source} · {t.ago(latest.age_hours ?? 0)}
              {latest.readings?.pm10 && prefs.pollutant === "pm25" && <> · PM10 {num(prefs.lang, latest.readings.pm10.value)} µg/m³</>}
            </div>
          </Card>
        )}

        <div>
        <SectionLabel>{t.nextHours}</SectionLabel>
        <Card>
          {win ? <><HoursStrip windows={win.windows} /><Legend />
            <p className="mt-4 text-[12px] leading-relaxed text-ink-3">{t.notSafety}</p></>
            : winErr ? <p className="text-[14px] text-ink-2">{winErr}</p> : <Skeleton className="h-44" />}
        </Card>
        </div>

        <Link href="/plan" className="block lg:col-span-2">
          <Card tone="accent" className="flex items-center justify-between">
            <span className="text-[17px] font-semibold">{t.planTitle}</span>
            <span className="text-accent" aria-hidden>›</span>
          </Card>
        </Link>
      </div>
    </>
  );
}
