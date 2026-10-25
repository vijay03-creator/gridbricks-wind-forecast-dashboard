const BASE = (import.meta.env.VITE_API_BASE_URL || "http://localhost:8000").replace(/\/$/, "");

async function get(path, params, signal) {
  const res = await fetch(`${BASE}${path}?${new URLSearchParams(params)}`, { signal });
  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`;
    try {
      const body = await res.json();
      if (typeof body.detail === "string") detail = body.detail;
    } catch {
      /* non-JSON error body */
    }
    throw new Error(detail);
  }
  return res.json();
}

export async function loadDashboard({ start, end, horizon }, signal) {
  const params = { start, end, horizon_hours: horizon };
  const [metrics, series] = await Promise.all([
    get("/api/metrics", params, signal),
    get("/api/series", params, signal),
  ]);
  return { metrics, points: series.points };
}
