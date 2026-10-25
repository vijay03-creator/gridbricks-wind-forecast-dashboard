"""FastAPI service exposing aligned wind actual-vs-forecast data and error metrics for January 2026."""
from __future__ import annotations

import logging
import os
import threading
from contextlib import asynccontextmanager
from datetime import date, timedelta
from functools import lru_cache

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from . import elexon
from .analysis import align, compute_metrics

logging.basicConfig(level=logging.INFO)

# Fixed analysis window: purchase decisions for January 2026 (UTC; GB local time equals UTC in January).
PERIOD_START = date(2026, 1, 1)
PERIOD_END = date(2026, 1, 31)
# Forecasts are fetched from before the window so the earliest intervals have candidates at any horizon.
FORECAST_LOOKBACK_DAYS = 14
MAX_HORIZON_HOURS = 168
DEFAULT_HORIZON_HOURS = 24

@asynccontextmanager
async def lifespan(_: FastAPI):
    """Warm the data cache in the background so the first visitor does not wait for upstream fetches."""
    def warm() -> None:
        try:
            load_data()
        except elexon.ElexonError as exc:
            logging.getLogger(__name__).warning("Startup warm-up failed; will retry on first request: %s", exc)

    threading.Thread(target=warm, daemon=True).start()
    yield


app = FastAPI(title="UK Wind Forecast Accuracy API", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if o.strip()],
    allow_methods=["GET"],
    allow_headers=["*"],
)


@lru_cache(maxsize=1)
def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Fetch (or read from disk cache) January actuals and the forecasts that could inform them."""
    actuals = elexon.fetch_actuals(PERIOD_START, PERIOD_END)
    forecasts = elexon.fetch_forecasts(PERIOD_START - timedelta(days=FORECAST_LOOKBACK_DAYS), PERIOD_END)
    return actuals, forecasts


def _aligned(start: date, end: date, horizon_hours: float) -> pd.DataFrame:
    if start > end:
        raise HTTPException(422, "start must be on or before end")
    if start < PERIOD_START or end > PERIOD_END:
        raise HTTPException(422, f"dates must be within {PERIOD_START} and {PERIOD_END}")
    try:
        actuals, forecasts = load_data()
    except elexon.ElexonError as exc:
        raise HTTPException(502, f"Upstream Elexon data unavailable: {exc}") from exc
    ts = lambda d: pd.Timestamp(d, tz="UTC")  # noqa: E731
    return align(actuals, forecasts, ts(start), ts(end + timedelta(days=1)), horizon_hours)


Start = Query(PERIOD_START, description="First UTC day (inclusive)")
End = Query(PERIOD_END, description="Last UTC day (inclusive)")
Horizon = Query(DEFAULT_HORIZON_HOURS, ge=0, le=MAX_HORIZON_HOURS,
                description="Hours before delivery at which the purchase decision is made")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/config")
def config() -> dict:
    return {
        "period_start": PERIOD_START, "period_end": PERIOD_END,
        "default_horizon_hours": DEFAULT_HORIZON_HOURS, "max_horizon_hours": MAX_HORIZON_HOURS,
    }


@app.get("/api/metrics")
def metrics(start: date = Start, end: date = End, horizon_hours: float = Horizon) -> dict:
    df = _aligned(start, end, horizon_hours)
    return {"start": start, "end": end, "horizon_hours": horizon_hours, **compute_metrics(df)}


@app.get("/api/series")
def series(start: date = Start, end: date = End, horizon_hours: float = Horizon) -> dict:
    df = _aligned(start, end, horizon_hours)
    points = [
        {
            "t": row.start.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "actual": None if pd.isna(row.actual) else round(float(row.actual), 1),
            "forecast": None if pd.isna(row.forecast) else round(float(row.forecast), 1),
            "error": None if pd.isna(row.error) else round(float(row.error), 1),
            "forecast_publish": None if pd.isna(row.forecast_publish)
            else row.forecast_publish.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        for row in df.itertuples()
    ]
    return {"start": start, "end": end, "horizon_hours": horizon_hours, "points": points}
