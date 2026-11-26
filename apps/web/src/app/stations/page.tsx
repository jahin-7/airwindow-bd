"use client";

import dynamic from "next/dynamic";
import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";
import { Card, LargeTitle, Skeleton } from "@/components/ui";
import { api, type Station } from "@/lib/api";
import { dict } from "@/lib/i18n";
import { usePrefs } from "@/lib/prefs";
import { useApi } from "@/lib/useApi";

const StationMap = dynamic(() => import("@/components/StationMap"), { ssr: false, loading: () => <Skeleton className="h-72" /> });

export default function Stations() {
  const { prefs, set } = usePrefs();
  const t = dict(prefs.lang);
  const router = useRouter();
  const [q, setQ] = useState("");
  const [locErr, setLocErr] = useState(false);

  const loc = useApi("locations", () => api.locations());
  const [near, setNear] = useState<Station[] | null>(null); // "use my location" re-sorts by distance
  const all = useMemo<Station[] | null>(() => near ?? loc.data ?? (loc.error ? [] : null), [near, loc.data, loc.error]);

  const shown = useMemo(() => {
    if (!all) return [];
    const s = q.trim().toLowerCase();
    return s ? all.filter((x) => x.name.toLowerCase().includes(s) || x.city.toLowerCase().includes(s) || x.name_bn.includes(q.trim())) : all;
  }, [all, q]);

  const pick = (id: string) => { set({ stationId: id }); router.push("/"); };

  const locate = () => {
    setLocErr(false);
    navigator.geolocation?.getCurrentPosition(
      (p) => api.nearby(p.coords.latitude, p.coords.longitude).then(setNear).catch(() => setLocErr(true)),
      () => setLocErr(true), { maximumAge: 600000, timeout: 10000 });
  };

  return (
    <>
      <LargeTitle title={t.stationsTitle} sub={t.coverageNote} />
      <div className="space-y-3 px-4">
        <input value={q} onChange={(e) => setQ(e.target.value)} placeholder={t.search} aria-label={t.search}
          className="w-full rounded-full bg-card px-5 py-3.5 text-[16px] outline-none placeholder:text-ink-3" />
        <button onClick={locate} className="flex w-full items-center gap-3 rounded-[22px] bg-accent-soft px-5 py-3.5 text-left">
          <span className="text-accent" aria-hidden>◎</span>
          <span className="flex-1"><span className="block font-semibold">{t.useLocation}</span>
            <span className="text-[12px] text-ink-2">{t.locationNote}</span></span>
        </button>
        {locErr && <p className="px-2 text-[13px] text-warn">{prefs.lang === "bn" ? "অবস্থান পাওয়া যায়নি। তালিকা থেকে বেছে নিন।" : "Couldn't get your location. Pick from the list instead."}</p>}
        {!prefs.lowData && all && all.length > 0 && <StationMap stations={all} selected={prefs.stationId} onPick={pick} lang={prefs.lang} />}
        <Card className="divide-y divide-line !py-1">
          {!all && <Skeleton className="my-4 h-40" />}
          {shown.map((s) => (
            <button key={s.id} onClick={() => pick(s.id)} className="flex w-full items-center gap-3 py-4 text-left">
              <span className={`h-3 w-3 rounded-full ${s.id === prefs.stationId ? "bg-accent" : "border-2 border-line"}`} aria-hidden />
              <span className="min-w-0 flex-1">
                <span className="block text-[16px] font-medium">{prefs.lang === "bn" ? s.name_bn : s.name}</span>
                <span className="text-[13px] text-ink-2">{s.distance_km != null ? t.kmAway(s.distance_km) : s.city}</span>
              </span>
              <span className="text-ink-3" aria-hidden>›</span>
            </button>
          ))}
        </Card>
      </div>
    </>
  );
}
