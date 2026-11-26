"use client";

import { useState } from "react";
import { Bar, BarChart, CartesianGrid, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Card, LargeTitle, Segmented, Skeleton } from "@/components/ui";
import { api } from "@/lib/api";
import { dict, num, toBn } from "@/lib/i18n";
import { usePrefs } from "@/lib/prefs";
import { useApi } from "@/lib/useApi";

const WHO = { pm25: 15, pm10: 45 } as const;

export default function Trends() {
  const { prefs, set } = usePrefs();
  const t = dict(prefs.lang);
  const [days, setDays] = useState("7");
  const tr = useApi(`trends:${prefs.stationId}:${days}`, () => api.trends(prefs.stationId, Number(days)));
  const data = tr.data ? tr.data.daily.map((d) => ({ date: d.date, v: prefs.pollutant === "pm25" ? d.pm25_mean : d.pm10_mean }))
    : tr.error ? [] : null;

  const label = (d: string) => {
    const s = `${Number(d.slice(8, 10))}/${Number(d.slice(5, 7))}`;
    return prefs.lang === "bn" ? toBn(s) : s;
  };

  return (
    <>
      <LargeTitle title={t.trendsTitle} sub={t.historicalNote} />
      <div className="space-y-3 px-4">
        <Segmented label="days" value={days} onChange={setDays} options={[{ value: "7", label: t.days7 }, { value: "30", label: t.days30 }]} />
        <Segmented label="trend-pollutant" value={prefs.pollutant} onChange={(v) => set({ pollutant: v })}
          options={[{ value: "pm25", label: "PM2.5" }, { value: "pm10", label: "PM10" }]} />
        <Card>
          <div className="text-[13px] font-medium text-ink-3">{t.daily} · µg/m³</div>
          {!data ? <Skeleton className="mt-3 h-64" /> : data.length === 0 ? <p className="mt-3 text-ink-2">{t.noData}</p> : (
            <div className="mt-3 h-64" role="img" aria-label={`${t.daily}: ${data.map((d) => `${label(d.date)} ${d.v ?? "–"}`).join(", ")}`}>
              <ResponsiveContainer>
                <BarChart data={data} margin={{ left: -18, right: 4, top: 8 }}>
                  <CartesianGrid vertical={false} stroke="var(--line)" />
                  <XAxis dataKey="date" tickFormatter={label} tick={{ fill: "var(--ink-3)", fontSize: 11 }} axisLine={false} tickLine={false}
                    interval={days === "30" ? 4 : 0} />
                  <YAxis tick={{ fill: "var(--ink-3)", fontSize: 11 }} axisLine={false} tickLine={false}
                    tickFormatter={(v) => num(prefs.lang, v)} />
                  <Tooltip cursor={{ fill: "var(--card-2)" }} contentStyle={{ background: "var(--card)", border: "none", borderRadius: 14, color: "var(--ink)" }}
                    labelFormatter={label} formatter={(v) => [`${num(prefs.lang, Number(v), 1)} µg/m³`, prefs.pollutant === "pm25" ? "PM2.5" : "PM10"]} />
                  <ReferenceLine y={WHO[prefs.pollutant]} stroke="var(--ink-2)" strokeDasharray="4 4"
                    label={{ value: "WHO", position: "insideTopRight", fill: "var(--ink-2)", fontSize: 11 }} />
                  <Bar dataKey="v" fill="var(--ink)" radius={[8, 8, 8, 8]} maxBarSize={28} isAnimationActive={!prefs.lowData} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
          <p className="mt-3 text-[12px] text-ink-3">
            {prefs.lang === "bn" ? "যেদিন ১৮ ঘণ্টার কম পরিমাপ আছে সেদিনের গড় দেখানো হয়নি। ড্যাশ লাইন: WHO ২৪-ঘণ্টা নির্দেশিকা।"
              : "Days with fewer than 18 hourly readings are left blank. Dashed line: WHO 24-hour guideline."}
          </p>
        </Card>
      </div>
    </>
  );
}
