"use client";

import { useEffect, useRef, useState } from "react";
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

/**
 * Loads [key] with [fetcher]. [keepPrevious] keeps the old data on screen while a new key loads,
 * for changes that re-rank the same items (like picking another activity).
 */
export function useApi<T>(key: string, fetcher: () => Promise<T>, keepPrevious = false): ApiState<T> {
  const [state, setState] = useState<{ data: T | null; error: string | null; loading: boolean }>(() => {
    const hit = cache.get(key);
    return { data: hit ? (hit.value as T) : null, error: null, loading: !hit };
  });
  const [tick, setTick] = useState(0);
  const fetch = useRef(fetcher);
  fetch.current = fetcher;

  useEffect(() => {
    let live = true;
    const hit = cache.get(key);
    setState((prev) => ({ data: hit ? (hit.value as T) : keepPrevious ? prev.data : null, error: null, loading: true }));
    if (hit && tick === 0 && Date.now() - hit.at < FRESH_MS) {
      setState((prev) => ({ ...prev, loading: false }));
      return;
    }
    fetch.current()
      .then((value) => {
        cache.set(key, { at: Date.now(), value });
        if (live) setState({ data: value, error: null, loading: false });
      })
      .catch((e) => {
        if (!live) return;
        const message = e instanceof ApiError ? e.message : "offline";
        setState((prev) => ({ data: prev.data, error: prev.data ? null : message, loading: false }));
      });
    return () => { live = false; };
  }, [key, tick, keepPrevious]);

  return { ...state, reload: () => setTick((n) => n + 1) };
}
