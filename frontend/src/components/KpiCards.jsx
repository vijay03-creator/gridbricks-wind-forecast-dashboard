const fmt = (v, digits = 0) =>
  v === null || v === undefined ? "–" : v.toLocaleString("en-GB", { maximumFractionDigits: digits, minimumFractionDigits: digits });

function Card({ label, value, unit, hint }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4">
      <dt className="text-sm font-medium text-slate-600">{label}</dt>
      <dd className="mt-1 text-2xl font-semibold tabular-nums">
        {value} <span className="text-sm font-normal text-slate-500">{unit}</span>
      </dd>
      <p className="mt-1 text-xs text-slate-500">{hint}</p>
    </div>
  );
}

export default function KpiCards({ metrics }) {
  const signed = metrics.bias_mw === null ? "–" : (metrics.bias_mw > 0 ? "+" : "") + fmt(metrics.bias_mw);
  return (
    <dl className="grid grid-cols-2 gap-4 lg:grid-cols-4">
      <Card label="Mean absolute error" value={fmt(metrics.mae_mw)} unit="MW" hint="Average size of a miss" />
      <Card label="Root mean square error" value={fmt(metrics.rmse_mw)} unit="MW" hint="Penalises large misses" />
      <Card label="Bias (forecast − actual)" value={signed} unit="MW"
        hint={metrics.bias_mw === null ? "" : metrics.bias_mw >= 0 ? "Positive = over-forecast" : "Negative = under-forecast"} />
      <Card label="Evaluated intervals" value={fmt(metrics.evaluated_intervals)} unit={`of ${fmt(metrics.expected_intervals)}`}
        hint={`30-min periods; MAPE ${metrics.mape_pct === null ? "–" : fmt(metrics.mape_pct, 1) + "%"} (actual ≥ ${metrics.mape_min_actual_mw} MW)`} />
    </dl>
  );
}
