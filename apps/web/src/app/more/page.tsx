"use client";

import { useEffect, useState } from "react";
import { Card, LargeTitle, Row, SectionLabel, Segmented, Toggle } from "@/components/ui";
import { api } from "@/lib/api";
import { dict, num } from "@/lib/i18n";
import { usePrefs } from "@/lib/prefs";

type Metric = { pollutant: string; horizon: number; model: string; mae: number; skill_vs_persistence?: number; interval80_coverage?: number };

export default function More() {
  const { prefs, set, reset } = usePrefs();
  const t = dict(prefs.lang);
  const [card, setCard] = useState<{ model_version?: string; overall?: Metric[] } | null>(null);
  const [toast, setToast] = useState<string | null>(null);

  useEffect(() => { api.modelCard().then((c) => setCard(c as typeof card)).catch(() => setCard(null)); }, []);

  const enableAlerts = async (on: boolean) => {
    if (on && "Notification" in window && Notification.permission === "default") {
      try { await Notification.requestPermission(); } catch {}
    }
    set({ alertsOn: on });
  };

  const rows = (card?.overall ?? []).filter((m) => m.pollutant === prefs.pollutant &&
    (m.model === "persistence" || m.model === "lightgbm_tgt_weather"));

  return (
    <>
      <LargeTitle title={t.moreTitle} />
      <div className="px-4">
        <SectionLabel>{t.settings}</SectionLabel>
        <Card className="space-y-5">
          <div>
            <div className="mb-2 text-[13px] font-medium text-ink-3">{t.language}</div>
            <Segmented label="lang" value={prefs.lang ?? "en"} onChange={(v) => set({ lang: v })}
              options={[{ value: "bn", label: "বাংলা" }, { value: "en", label: "English" }]} />
          </div>
          <div>
            <div className="mb-2 text-[13px] font-medium text-ink-3">{t.scale}</div>
            <div className="space-y-1">
              {([["doe", t.scaleDoe], ["epa", t.scaleEpa], ["ugm3", t.scaleUg]] as const).map(([v, l]) => (
                <Row key={v} title={l} onClick={() => set({ scale: v })}
                  right={<span className={`h-5 w-5 rounded-full border-2 ${prefs.scale === v ? "border-[6px] border-accent" : "border-line"}`} aria-hidden />} />
              ))}
            </div>
          </div>
          <div>
            <div className="mb-2 text-[13px] font-medium text-ink-3">{t.theme}</div>
            <Segmented label="theme" value={prefs.theme} onChange={(v) => set({ theme: v })}
              options={[{ value: "system", label: t.themeSystem }, { value: "light", label: t.themeLight }, { value: "dark", label: t.themeDark }]} />
          </div>
          <Row title={t.lowData} sub={t.lowDataSub} right={<Toggle label={t.lowData} on={prefs.lowData} onChange={(v) => set({ lowData: v })} />} />
        </Card>

        <SectionLabel>{t.alerts}</SectionLabel>
        <Card>
          <Row title={t.alertsOn} sub={t.alertsSub} right={<Toggle label={t.alertsOn} on={prefs.alertsOn} onChange={enableAlerts} />} />
          {prefs.alertsOn && (
            <div className="mt-2">
              <div className="mb-2 text-[13px] font-medium text-ink-3">{t.threshold} · PM2.5 µg/m³</div>
              <Segmented label="threshold" value={String(prefs.alertThreshold)} onChange={(v) => set({ alertThreshold: Number(v) })}
                options={[{ value: "35.5", label: num(prefs.lang, 35.5, 1) }, { value: "55.5", label: num(prefs.lang, 55.5, 1) }, { value: "125.5", label: num(prefs.lang, 125.5, 1) }]} />
              <p className="mt-2 text-[12px] text-ink-3">
                {prefs.lang === "bn" ? "এগুলো ২৪-ঘণ্টা AQI স্তরের সীমা (১০১, ১৫১, ২০১)।" : "These are the 24-hour AQI band edges (101, 151, 201)."}
              </p>
            </div>
          )}
        </Card>

        <SectionLabel>{t.method}</SectionLabel>
        <Card className="space-y-4 text-[14px] leading-relaxed">
          <p>{prefs.lang === "bn"
            ? "মডেল প্রশিক্ষণ: CAMS-BD — বাংলাদেশ পরিবেশ অধিদপ্তরের ১৬টি ক্রমাগত বায়ু পর্যবেক্ষণ স্টেশনের ঘণ্টাভিত্তিক পরিমাপ, নভেম্বর ২০১২–জানুয়ারি ২০২৫ (CC BY 4.0)। আবহাওয়া: Open-Meteo।"
            : "Training data: CAMS-BD — hourly measurements from Bangladesh DoE Continuous Air Monitoring Stations, Nov 2012–Jan 2025 (CC BY 4.0). Weather: Open-Meteo."}</p>
          <p>{prefs.lang === "bn"
            ? "AQI: পরিবেশ অধিদপ্তরের \"AQI Scheme for Bangladesh\" স্তর ও রং। ঘনত্ব থেকে সূচক রূপান্তরে US EPA (২০২৪) ব্রেকপয়েন্ট, ২৪-ঘণ্টা গড়ে। WHO ২০২১ নির্দেশিকা: PM2.5 ১৫, PM10 ৪৫ µg/m³ (২৪ ঘণ্টা)।"
            : "AQI: bands and colours from DoE's \"AQI Scheme for Bangladesh\"; concentration-to-index uses US EPA (2024) breakpoints on 24-hour means. WHO 2021 guideline: PM2.5 15, PM10 45 µg/m³ (24-hour)."}</p>
          {rows.length > 0 && (
            <div>
              <div className="mb-2 text-[13px] font-medium text-ink-3">
                {prefs.lang === "bn" ? "পরীক্ষার ফল (২০২৪, মডেল দেখেনি)" : "Test results (2024, unseen by the model)"} · {card?.model_version}
              </div>
              <table className="w-full text-[13px] tabular">
                <thead className="text-ink-3"><tr><th className="text-left font-medium">h</th><th className="text-right font-medium">MAE</th>
                  <th className="text-right font-medium">{prefs.lang === "bn" ? "উন্নতি" : "vs no-change"}</th></tr></thead>
                <tbody>
                  {[1, 3, 6].map((h) => {
                    const m = rows.find((r) => r.horizon === h && r.model.startsWith("lightgbm"));
                    return m && (
                      <tr key={h} className="border-t border-line">
                        <td className="py-1.5">+{num(prefs.lang, h)}h</td>
                        <td className="text-right">{num(prefs.lang, m.mae, 1)}</td>
                        <td className="text-right">{num(prefs.lang, 100 * (m.skill_vs_persistence ?? 0))}%</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
          <p className="text-[12px] text-ink-3">{prefs.lang === "bn"
            ? "এটি চিকিৎসা পরামর্শ নয়। তীব্র দূষণের সময় সরকারি স্বাস্থ্য পরামর্শ মেনে চলুন।"
            : "This is not medical advice. During severe pollution, follow official public-health advisories."}</p>
        </Card>

        <div className="mt-6">
          <button onClick={() => { reset(); setToast(t.deleted); }}
            className="w-full rounded-full bg-card py-4 text-[16px] font-semibold text-warn">{t.deleteAll}</button>
          {toast && <p role="status" className="mt-2 text-center text-[13px] text-ink-2">{toast}</p>}
        </div>
      </div>
    </>
  );
}
