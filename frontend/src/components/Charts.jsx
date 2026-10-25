import {
  Area, AreaChart, CartesianGrid, Legend, Line, LineChart, ReferenceLine,
  ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";

const COLORS = { actual: "#1d4ed8", forecast: "#c2410c", error: "#475569" };
const tick = (t) => `${t.slice(5, 10)} ${t.slice(11, 16)}`;
const mw = (v) => (v === null || v === undefined ? "no data" : `${Math.round(v).toLocaleString("en-GB")} MW`);

function Panel({ title, description, children }) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-4">
      <h2 className="text-lg font-semibold">{title}</h2>
      <p className="mb-3 text-sm text-slate-600">{description}</p>
      <div className="h-72 w-full sm:h-80">
        <ResponsiveContainer>{children}</ResponsiveContainer>
      </div>
    </section>
  );
}

const common = (points) => ({
  data: points,
  margin: { top: 8, right: 16, bottom: 0, left: 8 },
});

function axes() {
  return [
    <CartesianGrid key="g" strokeDasharray="3 3" stroke="#e2e8f0" />,
    <XAxis key="x" dataKey="t" tickFormatter={tick} minTickGap={48} tick={{ fontSize: 12 }}
      label={{ value: "Delivery time (UTC)", position: "insideBottom", offset: -2, fontSize: 12 }} height={40} />,
    <YAxis key="y" tick={{ fontSize: 12 }} width={64} tickFormatter={(v) => v.toLocaleString("en-GB")}
      label={{ value: "MW", angle: -90, position: "insideLeft", fontSize: 12 }} />,
  ];
}

export function GenerationChart({ points }) {
  return (
    <Panel title="Actual vs forecast wind generation"
      description="Forecast shown is the latest one published before the purchase decision cutoff. Gaps mean missing data.">
      <LineChart {...common(points)}>
        {axes()}
        <Tooltip labelFormatter={(t) => `${tick(t)} UTC`} formatter={(v, name) => [mw(v), name]} />
        <Legend verticalAlign="top" height={28} />
        <Line type="monotone" dataKey="actual" name="Actual" stroke={COLORS.actual} dot={false} strokeWidth={2}
          connectNulls={true} isAnimationActive={false} />
        <Line type="monotone" dataKey="forecast" name="Forecast" stroke={COLORS.forecast} dot={false} strokeWidth={2}
          strokeDasharray="6 3" connectNulls={true} isAnimationActive={false} />
      </LineChart>
    </Panel>
  );
}

export function ErrorChart({ points }) {
  return (
    <Panel title="Forecast error (forecast − actual)"
      description="Above zero the forecast was too high; below zero it was too low.">
      <AreaChart {...common(points)}>
        {axes()}
        <Tooltip labelFormatter={(t) => `${tick(t)} UTC`} formatter={(v) => [mw(v), "Error"]} />
        <ReferenceLine y={0} stroke="#0f172a" />
        <Area type="monotone" dataKey="error" name="Error" stroke={COLORS.error} fill={COLORS.error}
          fillOpacity={0.25} connectNulls={true} isAnimationActive={false} />
      </AreaChart>
    </Panel>
  );
}
