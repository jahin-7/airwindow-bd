"use client";

import { motion, useScroll, useTransform } from "motion/react";

/**
 * One UI-style large title: the top ~third of the screen holds a big title that
 * shrinks into a compact bar as you scroll, so content lands in thumb reach.
 */
export function LargeTitle({ title, sub, children }: { title: React.ReactNode; sub?: React.ReactNode; children?: React.ReactNode }) {
  const { scrollY } = useScroll();
  const big = useTransform(scrollY, [0, 140], [1, 0]);
  const shift = useTransform(scrollY, [0, 140], [0, -24]);
  const bar = useTransform(scrollY, [90, 150], [0, 1]);
  return (
    <>
      <motion.div style={{ opacity: bar }}
        className="fixed inset-x-0 top-0 z-30 flex h-14 lg:left-60 items-center justify-center bg-bg/90 px-4 text-[17px] font-semibold backdrop-blur pointer-events-none">
        <span className="max-w-[640px] truncate">{title}</span>
      </motion.div>
      <header className="flex min-h-[32svh] flex-col justify-end px-6 pb-6 pt-16 lg:min-h-[24vh] lg:px-4">
        <motion.div style={{ opacity: big, y: shift }}>
          <h1 className="text-[34px] font-semibold lg:text-[44px] leading-tight tracking-tight text-balance">{title}</h1>
          {sub && <div className="mt-2 text-[15px] text-ink-2">{sub}</div>}
          {children}
        </motion.div>
      </header>
    </>
  );
}

export function Card({ children, className = "", tone = "default", ...rest }: React.HTMLAttributes<HTMLDivElement> & { tone?: "default" | "warn" | "accent" }) {
  const bg = tone === "warn" ? "bg-warn-soft" : tone === "accent" ? "bg-accent-soft" : "bg-card";
  return (
    <motion.div layout initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}
      transition={{ type: "spring", stiffness: 380, damping: 32 }}
      className={`${bg} rounded-[var(--radius-card)] p-5 shadow-[var(--shadow)] ${className}`} {...(rest as object)}>
      {children}
    </motion.div>
  );
}

export function SectionLabel({ children }: { children: React.ReactNode }) {
  return <div className="px-2 pb-2 pt-5 text-[13px] font-medium text-ink-3">{children}</div>;
}

export function Segmented<T extends string>({ value, options, onChange, label }: {
  value: T; options: { value: T; label: string }[]; onChange: (v: T) => void; label: string;
}) {
  return (
    <div role="radiogroup" aria-label={label} className="flex rounded-full bg-card-2 p-1">
      {options.map((o) => {
        const on = o.value === value;
        return (
          <button key={o.value} role="radio" aria-checked={on} onClick={() => onChange(o.value)}
            className={`relative flex-1 rounded-full px-3 py-2 text-[14px] font-medium transition-colors ${on ? "text-ink" : "text-ink-2"}`}>
            {on && <motion.span layoutId={`seg-${label}`} className="absolute inset-0 rounded-full bg-card shadow-sm"
              transition={{ type: "spring", stiffness: 500, damping: 38 }} />}
            <span className="relative">{o.label}</span>
          </button>
        );
      })}
    </div>
  );
}

export function Toggle({ on, onChange, label }: { on: boolean; onChange: (v: boolean) => void; label: string }) {
  return (
    <button role="switch" aria-checked={on} aria-label={label} onClick={() => onChange(!on)}
      className={`relative h-[30px] w-[52px] shrink-0 rounded-full transition-colors ${on ? "bg-accent-fill" : "bg-card-2"}`}>
      <motion.span layout transition={{ type: "spring", stiffness: 600, damping: 35 }}
        className={`absolute top-[3px] h-6 w-6 rounded-full bg-white shadow ${on ? "right-[3px]" : "left-[3px]"}`} />
    </button>
  );
}

export function Row({ title, sub, right, onClick }: { title: React.ReactNode; sub?: React.ReactNode; right?: React.ReactNode; onClick?: () => void }) {
  const Comp = onClick ? "button" : "div";
  return (
    <Comp onClick={onClick} className="flex w-full items-center gap-4 py-3 text-left">
      <div className="min-w-0 flex-1">
        <div className="text-[16px]">{title}</div>
        {sub && <div className="mt-0.5 text-[13px] text-ink-2">{sub}</div>}
      </div>
      {right}
    </Comp>
  );
}

export function Skeleton({ className = "" }: { className?: string }) {
  return <div className={`animate-pulse rounded-2xl bg-card-2 ${className}`} />;
}

/** Measured values: solid ink. Forecast values: accent with a dashed underline. Never colour alone. */
export function KindTag({ kind, label }: { kind: "measured" | "forecast"; label: string }) {
  return kind === "measured" ? (
    <span className="inline-flex items-center gap-1.5 text-[12px] font-medium text-ink-2">
      <span className="h-2 w-2 rounded-full bg-ink" aria-hidden /> {label}
    </span>
  ) : (
    <span className="inline-flex items-center gap-1.5 text-[12px] font-medium text-forecast">
      <span className="h-2 w-2 rounded-full border-2 border-dashed border-forecast" aria-hidden /> {label}
    </span>
  );
}
