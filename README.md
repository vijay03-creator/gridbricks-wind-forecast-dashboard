# UK Wind Forecast Accuracy & Procurement Dashboard

Compares **actual** UK national wind generation with the **forecast that was available at purchase-decision time**, for January 2026, at 30-minute resolution. Data comes from the Elexon BMRS Insights API (FUELHH actuals, WINDFOR forecasts).

- **Live app:** `<add Vercel URL after deploying>`
- **Backend API:** `<add backend URL after deploying>` (`/health`, `/docs`)
- **Demo video:** `<add unlisted YouTube URL>`

> **AI assistance disclosure:** this project was designed and written with the help of an AI assistant (Claude, by Anthropic). Code, tests and documentation were AI-generated and then reviewed by the author. See [Testing](#testing) for exactly what was and was not verified.

## Directory layout

```
backend/                 FastAPI service (Python)
  app/elexon.py          fetch (chunked, retried), schema validation, on-disk JSON cache
  app/analysis.py        cutoff-based forecast selection, alignment, MAE/RMSE/bias/MAPE
  app/main.py            endpoints, date validation, CORS, cache warm-up
  tests/                 pytest: cutoff logic, alignment, metrics, parsing, API
  Dockerfile, requirements*.txt, pytest.ini
frontend/                React + Vite + Tailwind + Recharts
  src/App.jsx            page state (loading / error / empty / ready)
  src/api.js             API client
  src/insights.js(+test) data-driven insight text
  src/components/        Controls, KpiCards, Charts
  Dockerfile, nginx.conf, vercel.json
docker-compose.yml       backend :8000 + frontend :8080
.env.example             all environment variables
DEMO_SCRIPT.md           10-minute demo script
```

## Run it

**Docker (both services)**
```bash
docker compose up --build
# frontend http://localhost:8080   backend http://localhost:8000/docs
```
The first request fetches January from Elexon (a few dozen seconds) and caches it in a Docker volume; the backend also warms the cache on startup.

**Locally without Docker**
```bash
cd backend && python -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload            # http://localhost:8000

cd frontend && npm install
npm run dev                              # http://localhost:5173
```

## Method and assumptions

| Topic | Decision |
|---|---|
| Window | 1–31 Jan 2026, UTC (GB local time equals UTC in January, so no DST handling is needed). 1,488 half-hour intervals. |
| Decision time | A buyer commits **H hours before delivery** (default **24 h**, selectable 1–48 h in the UI, API accepts 0–168). For an interval starting at `T` the cutoff is `T − H`. |
| Forecast choice | Of all forecasts for `T`, take the **latest with `publishTime ≤ T − H`**. Forecasts published after the cutoff are never used (no look-ahead). Intervals with no eligible forecast are left empty, not filled. |
| Actuals | FUELHH rows with `fuelType = WIND`, field `generation` (MW). Duplicate intervals keep the latest revision. |
| Forecast data | WINDFOR `startTime`, `publishTime`, `generation` (MW). Forecasts are fetched from 14 days before the window so early-January intervals have candidates. Exact duplicate `(startTime, publishTime)` rows are collapsed. |
| Missing data | The grid contains every 30-min interval; metrics use only intervals with both actual and forecast. The KPI card and an insight line show how many were excluded. |
| Error sign | `error = forecast − actual`. Positive bias means over-forecasting. |
| MAPE | Computed only where actual ≥ 100 MW (MAPE is undefined at zero and unstable near it). The count of intervals used is returned as `mape_intervals`. |
| Timestamps | All parsed to timezone-aware UTC. |

**Caveat to check against live data:** the 30-minute grid is matched on exact `startTime`. If WINDFOR returns hourly target times, only the matching half-hours are evaluated and the "Evaluated intervals" KPI shows the reduced coverage. Decide whether to hold each hourly forecast flat across both half-hours and document that choice if so.

## API

| Endpoint | Purpose |
|---|---|
| `GET /health` | Liveness check |
| `GET /api/config` | Period bounds and horizon limits |
| `GET /api/metrics?start&end&horizon_hours` | `mae_mw`, `rmse_mw`, `bias_mw`, `mape_pct`, interval counts |
| `GET /api/series?start&end&horizon_hours` | Per-interval `actual`, `forecast`, `error`, `forecast_publish` |

Dates must lie within January 2026 and `start ≤ end` (otherwise 422). Upstream failures return 502 with a readable message.

## Testing

```bash
cd backend && pytest        # 17 tests
cd frontend && npm test     # 2 tests
cd frontend && npm run build
```

Backend tests cover cutoff selection (including a forecast published after the cutoff being ignored), grid alignment with gaps, metric values, MAPE exclusions, schema validation, de-duplication, and API behaviour with upstream data mocked.

Verification status when this was written:
- Backend tests, frontend tests and the production build passed locally.
- The fetch/cache/API path was exercised against a **local synthetic mock** of the Elexon endpoints, not the real API.
- **Not verified:** calls to the real Elexon API (the build sandbox could not reach it), the response schemas beyond Elexon's documented fields, Docker image builds, and any hosted deployment. Run the app once against live data and check the numbers before relying on them.

## Deployment

**1. Backend on Render (Docker)**
1. Push this repo to GitHub (public, anonymous repo name).
2. Render → New → Web Service → connect the repo.
3. Root Directory `backend`, Runtime **Docker**, Health Check Path `/health`.
4. Environment: `CORS_ORIGINS` = your Vercel URL (you can set a placeholder first and update it in step 2 below).
5. Deploy and note the URL, e.g. `https://xxxx.onrender.com`. Free instances sleep when idle and have no persistent disk, so the first request after a cold start re-fetches from Elexon.

**2. Frontend on Vercel**
1. Vercel → Add New Project → import the same repo.
2. Root Directory `frontend` (framework Vite is detected; `vercel.json` is included).
3. Environment variable `VITE_API_BASE_URL` = the Render URL (no trailing slash).
4. Deploy, then set `CORS_ORIGINS` on Render to the final Vercel URL (comma-separate multiple origins) and redeploy the backend.

Heroku also works for the backend with the same Dockerfile (container stack) and `CORS_ORIGINS` config.

## Attribution and limits

Contains BMRS data © Elexon Limited, used under the BMRS data licence. National-level data only; no weather or other inputs. This is an analysis of historical forecast accuracy, not a trading recommendation.
