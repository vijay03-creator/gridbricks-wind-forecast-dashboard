import { describe, expect, it } from "vitest";
import { buildInsights } from "./insights.js";

const metrics = { evaluated_intervals: 3, expected_intervals: 4, mae_mw: 200, bias_mw: -100 };
const points = [
  { t: "2026-01-01T00:00:00Z", error: 100 },
  { t: "2026-01-01T00:30:00Z", error: -1500 },
  { t: "2026-01-01T01:00:00Z", error: 200 },
  { t: "2026-01-01T01:30:00Z", error: null },
];

describe("buildInsights", () => {
  it("returns nothing when no intervals were evaluated", () => {
    expect(buildInsights({ evaluated_intervals: 0 }, [])).toEqual([]);
  });

  it("describes direction, worst miss, share within 1,000 MW and exclusions", () => {
    const text = buildInsights(metrics, points).join("\n");
    expect(text).toContain("under-forecast wind output by 100 MW");
    expect(text).toContain("Largest miss: 1,500 MW under at 2026-01-01 00:30 UTC");
    expect(text).toContain("67% of evaluated intervals");
    expect(text).toContain("1 of 4 intervals were excluded");
  });
});
