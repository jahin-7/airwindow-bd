import { describe, expect, test } from "vitest";
import { clock, dict, num, toBn } from "@/lib/i18n";

describe("Bangla formatting", () => {
  test("digits", () => {
    expect(toBn(2024)).toBe("২০২৪");
    expect(num("bn", 55.46, 1)).toBe("৫৫.৫");
    expect(num("en", 55.46)).toBe("55");
  });

  test("clock reads the API's Dhaka wall time without converting time zones", () => {
    expect(clock("en", "2026-11-26T00:00:00")).toMatch(/^12/);
    expect(clock("en", "2026-11-26T14:00:00")).toMatch(/^2/);
    expect(clock("bn", "2026-11-26T14:00:00")).toBe("দুপুর ২টা");
    expect(clock("bn", "2026-11-26T05:00:00")).toBe("রাত ৫টা");
  });
});

test("every English string has a Bangla translation", () => {
  const en = dict("en"), bn = dict("bn");
  expect(Object.keys(bn).sort()).toEqual(Object.keys(en).sort());
  for (const [k, v] of Object.entries(bn)) if (typeof v === "string") expect(v.trim(), k).not.toBe("");
});
