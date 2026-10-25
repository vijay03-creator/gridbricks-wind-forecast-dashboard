const fmt = (n) => Math.round(n).toLocaleString("en-GB");

/** Plain-language findings derived only from the metrics and series returned by the API. */
export function buildInsights(metrics, points) {
  if (!metrics || metrics.evaluated_intervals === 0) return [];
  const out = [];

  const direction = metrics.bias_mw >= 0 ? "over-forecast" : "under-forecast";
  out.push(
    `On average the forecast ${direction} wind output by ${fmt(Math.abs(metrics.bias_mw))} MW ` +
      `(mean absolute error ${fmt(metrics.mae_mw)} MW). ` +
      (metrics.bias_mw >= 0
        ? "Buyers relying on it would tend to hold less cover than needed."
        : "Buyers relying on it would tend to hold more cover than needed.")
  );

  const rows = points.filter((p) => p.error !== null);
  const worst = rows.reduce((a, b) => (Math.abs(b.error) > Math.abs(a.error) ? b : a));
  out.push(
    `Largest miss: ${fmt(Math.abs(worst.error))} MW ${worst.error >= 0 ? "over" : "under"} ` +
      `at ${worst.t.slice(0, 16).replace("T", " ")} UTC.`
  );

  const within = rows.filter((p) => Math.abs(p.error) <= 1000).length;
  out.push(`${Math.round((within / rows.length) * 100)}% of evaluated intervals were within 1,000 MW of actual.`);

  const byHour = new Map();
  for (const p of rows) {
    const h = Number(p.t.slice(11, 13));
    const cur = byHour.get(h) || { sum: 0, n: 0 };
    cur.sum += Math.abs(p.error);
    cur.n += 1;
    byHour.set(h, cur);
  }
  const [hour, agg] = [...byHour.entries()].reduce((a, b) => (b[1].sum / b[1].n > a[1].sum / a[1].n ? b : a));
  out.push(`Errors are largest around ${String(hour).padStart(2, "0")}:00 UTC (mean ${fmt(agg.sum / agg.n)} MW).`);

  const missing = metrics.expected_intervals - metrics.evaluated_intervals;
  if (missing > 0) {
    out.push(
      `${missing} of ${metrics.expected_intervals} intervals were excluded because an actual or an eligible forecast was missing.`
    );
  }
  return out;
}
