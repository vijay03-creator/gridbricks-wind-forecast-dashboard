const HORIZONS = [1, 6, 12, 24, 48];

const inputCls =
  "mt-1 block w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-600/30";

export default function Controls({ filters, onChange, min, max }) {
  const set = (patch) => onChange({ ...filters, ...patch });
  const invalid = filters.start > filters.end;

  return (
    <form
      className="grid grid-cols-1 gap-4 rounded-lg border border-slate-200 bg-white p-4 sm:grid-cols-3"
      onSubmit={(e) => e.preventDefault()}
      aria-label="Analysis filters"
    >
      <label className="text-sm font-medium text-slate-700">
        Start date (UTC)
        <input type="date" className={inputCls} min={min} max={filters.end || max} value={filters.start}
          onChange={(e) => e.target.value && set({ start: e.target.value })} />
      </label>
      <label className="text-sm font-medium text-slate-700">
        End date (UTC)
        <input type="date" className={inputCls} min={filters.start || min} max={max} value={filters.end}
          onChange={(e) => e.target.value && set({ end: e.target.value })} />
      </label>
      <label className="text-sm font-medium text-slate-700">
        Decision lead time
        <select className={inputCls} value={filters.horizon}
          onChange={(e) => set({ horizon: Number(e.target.value) })}>
          {HORIZONS.map((h) => (
            <option key={h} value={h}>{h} h before delivery</option>
          ))}
        </select>
      </label>
      {invalid && (
        <p role="alert" className="text-sm text-red-700 sm:col-span-3">Start date must be on or before the end date.</p>
      )}
    </form>
  );
}
