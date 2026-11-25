"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { AnimatePresence, motion } from "motion/react";
import { useEffect, useState } from "react";
import { api, type Meta } from "@/lib/api";
import { dict } from "@/lib/i18n";
import { PrefsProvider, usePrefs } from "@/lib/prefs";

const TABS = [
  { href: "/", key: "navToday", icon: "M12 3v2m0 14v2m9-9h-2M5 12H3m15.4-6.4-1.4 1.4M7 17l-1.4 1.4m0-12.8L7 7m10 10 1.4 1.4M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8Z" },
  { href: "/plan", key: "navPlan", icon: "M8 3v3m8-3v3M4 9h16M5 6h14a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1Zm4 8 2 2 4-4" },
  { href: "/stations", key: "navMap", icon: "M12 21s-7-6.2-7-11a7 7 0 1 1 14 0c0 4.8-7 11-7 11Zm0-8.5a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5Z" },
  { href: "/trends", key: "navTrends", icon: "M4 19h16M6 16l4-5 3 3 5-7" },
  { href: "/more", key: "navMore", icon: "M5 12h.01M12 12h.01M19 12h.01" },
] as const;

function BottomNav() {
  const path = usePathname();
  const { prefs } = usePrefs();
  const t = dict(prefs.lang);
  return (
    <nav aria-label="Main" className="fixed inset-x-0 bottom-0 z-40 border-t border-line bg-bg/95 pb-[env(safe-area-inset-bottom)] backdrop-blur lg:inset-y-0 lg:right-auto lg:w-60 lg:border-r lg:border-t-0 lg:pb-0">
      <div className="hidden px-6 pb-8 pt-10 text-[20px] font-semibold lg:block">AirWindow <span className="text-accent">BD</span></div>
      <ul className="mx-auto flex max-w-[640px] lg:flex-col lg:gap-1 lg:px-3">
        {TABS.map((tab) => {
          const on = tab.href === "/" ? path === "/" : path.startsWith(tab.href);
          return (
            <li key={tab.href} className="flex-1">
              <Link href={tab.href} aria-current={on ? "page" : undefined}
                className="relative flex flex-col items-center gap-1 py-2.5 text-[11px] font-medium lg:flex-row lg:gap-3 lg:rounded-full lg:px-4 lg:py-3 lg:text-[15px]">
                {on && <motion.span layoutId="tab-pill" className="absolute top-1.5 h-8 w-14 rounded-full bg-accent-soft lg:inset-0 lg:h-auto lg:w-auto"
                  transition={{ type: "spring", stiffness: 500, damping: 40 }} />}
                <svg viewBox="0 0 24 24" className={`relative h-6 w-6 ${on ? "text-accent" : "text-ink-2"}`} fill="none"
                  stroke="currentColor" strokeWidth={on ? 2.2 : 1.8} strokeLinecap="round" strokeLinejoin="round" aria-hidden>
                  <path d={tab.icon} />
                </svg>
                <span className={`relative ${on ? "text-ink" : "text-ink-2"}`}>{t[tab.key]}</span>
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}

function Onboarding() {
  const { set } = usePrefs();
  const [pick, setPick] = useState<"bn" | "en">("bn");
  const t = dict(pick);
  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex flex-col bg-bg px-6 pb-10 pt-[18svh]">
      <div className="mx-auto flex w-full max-w-[480px] flex-1 flex-col">
        <div className="text-[15px] font-medium text-accent">AirWindow · এয়ারউইন্ডো</div>
        <h1 className="mt-3 text-[34px] font-semibold leading-tight">{t.chooseLang}</h1>
        <p className="mt-2 text-ink-2">{t.chooseLangSub}</p>
        <div className="mt-auto space-y-3">
          {([["bn", "বাংলা", "Bangla"], ["en", "English", "ইংরেজি"]] as const).map(([v, a, b]) => (
            <button key={v} onClick={() => setPick(v)} aria-pressed={pick === v}
              className={`flex w-full items-center justify-between rounded-[22px] border-2 bg-card px-5 py-4 text-left transition-colors ${pick === v ? "border-accent" : "border-transparent"}`}>
              <span><span className="block text-[18px] font-semibold">{a}</span><span className="text-[13px] text-ink-2">{b}</span></span>
              <span className={`h-6 w-6 rounded-full border-2 ${pick === v ? "border-accent bg-accent" : "border-line"}`} aria-hidden />
            </button>
          ))}
          <button onClick={() => set({ lang: pick })}
            className="mt-4 w-full rounded-full bg-accent-fill py-4 text-[17px] font-semibold text-white active:scale-[0.98]">
            {t.continue}
          </button>
        </div>
      </div>
    </motion.div>
  );
}

export function ReplayBanner() {
  const { prefs } = usePrefs();
  const [meta, setMeta] = useState<Meta | null>(null);
  useEffect(() => {
    api.meta().then(setMeta).catch(() => setMeta(null));
  }, []);
  if (meta?.mode !== "replay") return null;
  const t = dict(prefs.lang);
  return (
    <div role="status" className="mx-4 mb-3 rounded-[20px] lg:mb-4 bg-warn-soft px-4 py-3 text-[13px] leading-snug">
      <div className="font-semibold text-warn">{t.replayTitle}</div>
      <div className="mt-0.5 text-ink-2">{t.replaySub}</div>
    </div>
  );
}

/** While the app is open, check the latest measurement every 15 min against the user's threshold. */
function AlertWatcher() {
  const { prefs } = usePrefs();
  const [msg, setMsg] = useState<string | null>(null);
  useEffect(() => {
    if (!prefs.alertsOn) return;
    let lastSeen = "";
    const check = () => api.latest(prefs.stationId).then((l) => {
      const r = l.readings?.pm25;
      if (l.status !== "ok" || !r || r.observed_at === lastSeen || r.value < prefs.alertThreshold) return;
      lastSeen = r.observed_at;
      const t = dict(prefs.lang);
      const text = `PM2.5 ${r.value} µg/m³ (${t.measured}) · ${prefs.lang === "bn" ? l.station.name_bn : l.station.name}`;
      if ("Notification" in window && Notification.permission === "granted") new Notification("AirWindow", { body: text });
      else setMsg(text);
    }).catch(() => {});
    check();
    const id = setInterval(check, 15 * 60 * 1000);
    return () => clearInterval(id);
  }, [prefs.alertsOn, prefs.stationId, prefs.alertThreshold, prefs.lang]);
  if (!msg) return null;
  return (
    <button onClick={() => setMsg(null)} role="alert"
      className="fixed inset-x-4 bottom-24 z-40 lg:bottom-8 lg:left-64 mx-auto max-w-[600px] rounded-[20px] bg-ink px-5 py-4 text-left text-[14px] text-bg shadow-lg">
      {msg}
    </button>
  );
}

function Inner({ children }: { children: React.ReactNode }) {
  const { prefs, ready } = usePrefs();
  return (
    <>
      <div className="lg:pl-60">
        <main className="mx-auto min-h-svh max-w-[640px] pb-28 lg:max-w-[1040px] lg:px-6 lg:pb-12">{ready ? children : null}</main>
      </div>
      <BottomNav />
      <AlertWatcher />
      <AnimatePresence>{ready && !prefs.lang && <Onboarding />}</AnimatePresence>
    </>
  );
}

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <PrefsProvider>
      <Inner>{children}</Inner>
    </PrefsProvider>
  );
}
