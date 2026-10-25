import { useEffect, useMemo, useState } from "react";
import { loadDashboard } from "./api.js";
import { buildInsights } from "./insights.js";
import Controls from "./components/Controls.jsx";
import KpiCards from "./components/KpiCards.jsx";
import { ErrorChart, GenerationChart } from "./components/Charts.jsx";

const MIN = "2026-01-01";
const MAX = "2026-01-31";
const DEFAULT = { start: MIN, end: MAX, horizon: 24 };

export default function App() {
  const [filters, setFilters] = useState(DEFAULT);
  const [state, setState] = useState({ status: "loading" });

  useEffect(() => {
    if (filters.start > filters.end) return undefined;
    const ctrl = new AbortController();
    setState({ status: "loading" });
    loadDashboard(filters, ctrl.signal)
      .then((data) => setState({ status: "ready", ...data }))
      .catch((err) => {
        if (err.name !== "AbortError") setState({ status: "error", message: err.message });
      });
    return () => ctrl.abort();
  }, [filters]);

  const insights = useMemo(
    () => (state.status === "ready" ? buildInsights(state.metrics, state.points) : []),
    [state]
  );
  const empty = state.status === "ready" && state.metrics.evaluated_intervals === 0;

  return (
    <div className="mx-auto max-w-6xl px-4 py-6 sm:px-6">
      <header className="mb-6">
        <h1 className="text-2xl font-bold sm:text-3xl">UK wind forecast accuracy</h1>
        <p className="mt-1 text-slate-600">
          How well day-ahead wind forecasts matched actual national generation, for January 2026 purchase decisions.
        </p>
      </header>

      <div className="space-y-6">
        <Controls filters={filters} onChange={setFilters} min={MIN} max={MAX} />

        <div aria-live="polite">
          {state.status === "loading" && (
            <p className="rounded-lg border border-slate-200 bg-white p-6 text-slate-600">
              Loading Elexon data. The first request can take a minute while data is fetched and cached.
            </p>
          )}
          {state.status === "error" && (
            <div role="alert" className="rounded-lg border border-red-200 bg-red-50 p-6 text-red-800">
              <p className="font-semibold">Could not load data</p>
              <p className="text-sm">{state.message}</p>
              <button type="button" onClick={() => setFilters({ ...filters })}
                className="mt-3 rounded-md bg-red-700 px-3 py-1.5 text-sm font-medium text-white hover:bg-red-800 focus:outline-none focus:ring-2 focus:ring-red-700/40">
                Retry
              </button>
            </div>
          )}
          {empty && (
            <p className="rounded-lg border border-slate-200 bg-white p-6 text-slate-700">
              No intervals have both an actual and an eligible forecast for this selection. Try a longer date range or a
              shorter decision lead time.
            </p>
          )}
        </div>

        {state.status === "ready" && !empty && (
          <>
            <KpiCards metrics={state.metrics} />
            <GenerationChart points={state.points} />
            <ErrorChart points={state.points} />
            <section className="rounded-lg border border-slate-200 bg-white p-4">
              <h2 className="text-lg font-semibold">Insights</h2>
              <ul className="mt-2 list-disc space-y-1 pl-5 text-slate-700">
                {insights.map((line) => <li key={line}>{line}</li>)}
              </ul>
            </section>
          </>
        )}
      </div>

      <footer className="mt-8 border-t border-slate-200 pt-4 text-sm text-slate-600">
        <p>
          Contains BMRS data © Elexon Limited, from the Elexon Insights Solution (FUELHH actual wind generation, WINDFOR
          wind forecasts). Each interval uses the latest forecast published at least the chosen lead time before
          delivery, so no later information is used. MAPE only counts intervals with actual output of at least{" "}
          100 MW.
        </p>
      </footer>
    </div>
  );
}
