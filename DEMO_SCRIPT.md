# Demo script (max 10 minutes)

Record screen + voice, upload to YouTube as **Unlisted**, and test the link in an incognito window. Replace bracketed numbers with what the live dashboard shows. Do not quote figures you have not seen on screen.

## Part 1: Customer walkthrough (about 5:00)

**0:00 Problem (30 s)**
"If you buy power ahead of delivery, wind forecasts drive your volume. A forecast that is too high leaves you short; too low and you overbuy. This pilot measures how good the forecasts actually were for January 2026, using only what was known at decision time."

**0:30 Headline numbers (60 s)** Show the KPI cards.
"On average the forecast missed by [MAE] MW, with a typical large miss of [RMSE] MW. Bias is [bias] MW, which means the forecast tended to [over/under]-predict. [N] half-hour periods were evaluated."

**1:30 Actual vs forecast chart (90 s)** Hover a few points.
"Blue is what the wind farms delivered, orange dashed is the forecast available [24] hours earlier. Here it tracks well; here it misses [pick the visible worst episode]." Point to the insight list for the largest miss and the hour of day with the biggest errors.

**3:00 Error chart (45 s)**
"Above zero is over-forecast, below zero is under-forecast. Errors cluster in [periods], which is where cover decisions carry most risk."

**3:45 Lead time and dates (60 s)** Change lead time from 24 h to 6 h, then narrow the date range.
"Shorter lead time gives fresher forecasts and the error [falls/changes] to [MAE]. You can zoom to any window in January."

**4:45 Close (15 s)**
"Next steps: extend beyond January, add price data, and turn accuracy into a recommended hedge volume."

## Part 2: Tech lead review (about 5:00)

**5:00 Architecture (60 s)** Open README layout section.
"React/Vite/Tailwind/Recharts frontend, FastAPI + pandas backend, two Dockerfiles and a compose file. Frontend on Vercel, backend on Render. The browser only talks to the backend; Elexon is never called from the client."

**6:00 Data layer, `backend/app/elexon.py` (60 s)**
"Fetches FUELHH and WINDFOR in 7-day chunks with retries, validates required fields, and caches each chunk on disk because historical data does not change. Parsing normalises to UTC and removes duplicates."

**7:00 The key logic, `backend/app/analysis.py` (90 s)** Show `select_forecasts`.
"Cutoff is delivery start minus the lead time. We keep only forecasts with `publishTime <= cutoff` and take the latest per interval. That is the whole no-look-ahead guarantee, and there is a test where a later forecast with a very different value must be ignored." Then `align` (full 30-min grid, gaps kept as NaN) and `compute_metrics` (MAPE excludes actuals under 100 MW and reports how many intervals it used).

**8:30 API and frontend (60 s)** Show `main.py` endpoints and `App.jsx`.
"Dates are validated to January, upstream failure returns 502, and the UI has explicit loading, error with retry, and empty states. Insights are computed from the returned data, nothing hard-coded."

**9:30 Tests, assumptions, AI use (30 s)** Run `pytest` and `npm test` on screen.
"Tests cover cutoff, alignment, metrics and parsing. Assumptions are in the README: 24 h default decision time, UTC, MAPE threshold. I built this with AI assistance and reviewed it; the README says so. Known limits: national data only, and WINDFOR time granularity should be confirmed against live data."

## Before recording
- Open the live app and let data load once so the demo is not waiting on Elexon.
- Check the numbers you will quote on screen after the final deploy.
