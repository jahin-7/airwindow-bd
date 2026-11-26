import { act, renderHook, waitFor } from "@testing-library/react";
import { expect, test, vi } from "vitest";
import { ApiError } from "@/lib/api";
import { useApi } from "@/lib/useApi";

// These pin down the fix for pages jumping: data must not disappear while it refreshes.

test("a page opened again shows its last data immediately", async () => {
  const fetcher = vi.fn().mockResolvedValue({ v: 1 });
  const first = renderHook(() => useApi("t1", fetcher));
  await waitFor(() => expect(first.result.current.data).toEqual({ v: 1 }));
  first.unmount();

  const again = renderHook(() => useApi("t1", fetcher));
  expect(again.result.current.data).toEqual({ v: 1 }); // first render, no skeleton
  expect(fetcher).toHaveBeenCalledTimes(1); // still fresh, not refetched
});

test("keepPrevious holds the old list while a new key loads", async () => {
  let resolve!: (v: string) => void;
  const fetchers: Record<string, () => Promise<string>> = {
    walk: () => Promise.resolve("walk list"),
    run: () => new Promise((r) => { resolve = r; }),
  };
  const { result, rerender } = renderHook(({ k }) => useApi(`t2:${k}`, fetchers[k], true), { initialProps: { k: "walk" } });
  await waitFor(() => expect(result.current.data).toBe("walk list"));

  rerender({ k: "run" });
  expect(result.current.data).toBe("walk list");
  await act(async () => resolve("run list"));
  expect(result.current.data).toBe("run list");
});

test("without keepPrevious a new key starts empty", async () => {
  const { result, rerender } = renderHook(({ k }) => useApi(`t3:${k}`, () => Promise.resolve(k)), { initialProps: { k: "a" } });
  await waitFor(() => expect(result.current.data).toBe("a"));
  rerender({ k: "b" });
  expect(result.current.data).toBeNull();
  await waitFor(() => expect(result.current.data).toBe("b"));
});

test("a failed refresh keeps the good data and shows no error", async () => {
  const fetcher = vi.fn().mockResolvedValueOnce("good").mockRejectedValueOnce(new Error("network"));
  const { result } = renderHook(() => useApi("t4", fetcher));
  await waitFor(() => expect(result.current.data).toBe("good"));
  act(() => result.current.reload());
  await waitFor(() => expect(result.current.loading).toBe(false));
  expect(result.current.data).toBe("good");
  expect(result.current.error).toBeNull();
});

test("with nothing to show, the API's message comes through", async () => {
  const { result } = renderHook(() => useApi("t5", () => Promise.reject(new ApiError(404, "Unknown station"))));
  await waitFor(() => expect(result.current.error).toBe("Unknown station"));
});
