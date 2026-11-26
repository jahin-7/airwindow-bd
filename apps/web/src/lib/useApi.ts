"use client";

import { useEffect, useEffectEvent, useState } from "react";
import { ApiError } from "@/lib/api";

// Responses kept for the life of the tab. Going back to a page shows what it showed last time
// straight away (and refreshes it quietly), instead of a skeleton that the real card then pushes
// past, which made the page jump and lose its place.
const cache = new Map<string, { at: number; value: unknown }>();
const FRESH_MS = 60_000;

export interface ApiState<T> {
  data: T | null;
  /** Only set when there's nothing to show; a failed refresh keeps the last good data. */
  error: string | null;
  loading: boolean;
  reload: () => void;
}

interface Held<T> { key: string; data: T | null; error: string | null; loading: boolean }

function start<T>(key: string, previous: T | null): Held<T> {
  const hit = cache.get(key);
  return { key, data: hit ? (hit.value as T) : previous, error: null, loading: !hit };
}

/**
 * Loads [key] with [fetcher]. [keepPrevious] keeps the old data on screen while a new key loads,
 * for changes that re-rank the same items (like picking another activity).
 */
export function useApi<T>(key: string, fetcher: () => Promise<T>, keepPrevious = false): ApiState<T> {
  const [held, setHeld] = useState<Held<T>>(() => start<T>(key, null));
  const [tick, setTick] = useState(0);

  // A new key: switch what's shown during this render, so there's no frame of stale content.
  let state = held;
  if (held.key !== key) {
    state = start<T>(key, keepPrevious ? held.data : null);
    setHeld(state);
  }

  const run = useEffectEvent(fetcher);

  useEffect(() => {
    const hit = cache.get(key);
    if (hit && tick === 0 && Date.now() - hit.at < FRESH_MS) return;
    let live = true;
    run()
      .then((value) => {
        cache.set(key, { at: Date.now(), value });
        if (live) setHeld({ key, data: value, error: null, loading: false });
      })
      .catch((e) => {
        if (!live) return;
        const message = e instanceof ApiError ? e.message : "offline";
        setHeld((h) => (h.key !== key ? h : { ...h, error: h.data ? null : message, loading: false }));
      });
    return () => { live = false; };
  }, [key, tick]);

  return {
    data: state.data, error: state.error, loading: state.loading,
    reload: () => { setHeld((h) => ({ ...h, loading: true })); setTick((n) => n + 1); },
  };
}
