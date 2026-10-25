"""Elexon BMRS client: fetch, validate and cache FUELHH (actuals) and WINDFOR (forecasts).

Endpoints (Insights API, JSON streams):
  GET /datasets/FUELHH/stream?settlementDateFrom&settlementDateTo&fuelType=WIND
      fields used: startTime, generation (fuelType is re-checked client side)
  GET /datasets/WINDFOR/stream?publishDateTimeFrom&publishDateTimeTo
      fields used: startTime, publishTime, generation

Windows are fetched in small chunks. Historical windows never change, so each
chunk is cached on disk as JSON and re-used on later runs.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import httpx
import pandas as pd

log = logging.getLogger(__name__)

BASE_URL = os.getenv("ELEXON_BASE_URL", "https://data.elexon.co.uk/bmrs/api/v1")
CACHE_DIR = Path(os.getenv("CACHE_DIR", ".cache"))
CHUNK_DAYS = 7
REQUEST_TIMEOUT_S = 60
MAX_ATTEMPTS = 3

ACTUAL_FIELDS = {"startTime", "generation"}
FORECAST_FIELDS = {"startTime", "publishTime", "generation"}


class ElexonError(RuntimeError):
    """Raised when the upstream API is unreachable or returns unexpected data."""


def _cache_path(name: str, params: dict) -> Path:
    key = hashlib.sha256(json.dumps([name, params], sort_keys=True).encode()).hexdigest()[:20]
    return CACHE_DIR / f"{name}-{key}.json"


def _get_json(client: httpx.Client, path: str, params: dict) -> list[dict]:
    last: Exception | None = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            resp = client.get(f"{BASE_URL}{path}", params=params, timeout=REQUEST_TIMEOUT_S)
            resp.raise_for_status()
            data = resp.json()
            if not isinstance(data, list):
                raise ElexonError(f"{path}: expected a JSON array, got {type(data).__name__}")
            return data
        except (httpx.HTTPError, ValueError) as exc:
            last = exc
            log.warning("Elexon request failed (%s/%s) %s: %s", attempt, MAX_ATTEMPTS, path, exc)
            time.sleep(1.5 * attempt)
    raise ElexonError(f"Elexon request to {path} failed after {MAX_ATTEMPTS} attempts: {last}")


def _cached_fetch(client: httpx.Client, name: str, path: str, params: dict) -> list[dict]:
    cache_file = _cache_path(name, params)
    if cache_file.exists():
        return json.loads(cache_file.read_text())
    rows = _get_json(client, path, params)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(json.dumps(rows))
    return rows


def _windows(start: date, end: date, days: int):
    """Yield inclusive (from, to) date windows covering [start, end]."""
    cur = start
    while cur <= end:
        nxt = min(cur + timedelta(days=days - 1), end)
        yield cur, nxt
        cur = nxt + timedelta(days=1)


def parse_actuals(rows: list[dict]) -> pd.DataFrame:
    """Validate raw FUELHH rows and return UTC `start` / `actual` columns (MW)."""
    if not rows:
        return pd.DataFrame({"start": pd.DatetimeIndex([], tz="UTC"), "actual": pd.Series(dtype=float)})
    df = pd.DataFrame(rows)
    missing = ACTUAL_FIELDS - set(df.columns)
    if missing:
        raise ElexonError(f"FUELHH response is missing fields: {sorted(missing)}")
    if "fuelType" in df.columns:
        df = df[df["fuelType"] == "WIND"]
    out = pd.DataFrame(
        {
            "start": pd.to_datetime(df["startTime"], utc=True, errors="coerce"),
            "actual": pd.to_numeric(df["generation"], errors="coerce"),
        }
    )
    if "publishTime" in df.columns:  # keep the latest revision of an interval
        out["_pub"] = pd.to_datetime(df["publishTime"], utc=True, errors="coerce")
        out = out.sort_values("_pub").drop(columns="_pub")
    out = out.dropna().drop_duplicates("start", keep="last")
    return out.sort_values("start").reset_index(drop=True)


def parse_forecasts(rows: list[dict]) -> pd.DataFrame:
    """Validate raw WINDFOR rows and return UTC `start` / `publish` / `forecast` columns (MW)."""
    if not rows:
        return pd.DataFrame(
            {
                "start": pd.DatetimeIndex([], tz="UTC"),
                "publish": pd.DatetimeIndex([], tz="UTC"),
                "forecast": pd.Series(dtype=float),
            }
        )
    df = pd.DataFrame(rows)
    missing = FORECAST_FIELDS - set(df.columns)
    if missing:
        raise ElexonError(f"WINDFOR response is missing fields: {sorted(missing)}")
    out = pd.DataFrame(
        {
            "start": pd.to_datetime(df["startTime"], utc=True, errors="coerce"),
            "publish": pd.to_datetime(df["publishTime"], utc=True, errors="coerce"),
            "forecast": pd.to_numeric(df["generation"], errors="coerce"),
        }
    ).dropna()
    out = out.drop_duplicates(["start", "publish"], keep="last")
    return out.sort_values(["start", "publish"]).reset_index(drop=True)


def fetch_actuals(start: date, end: date) -> pd.DataFrame:
    """Actual national wind generation (MW) per 30-min settlement period, start/end inclusive (UTC dates)."""
    rows: list[dict] = []
    with httpx.Client() as client:
        for lo, hi in _windows(start, end, CHUNK_DAYS):
            params = {
                "settlementDateFrom": lo.isoformat(),
                "settlementDateTo": hi.isoformat(),
                "fuelType": "WIND",
                "format": "json",
            }
            rows += _cached_fetch(client, "fuelhh", "/datasets/FUELHH/stream", params)
    return parse_actuals(rows)


def fetch_forecasts(publish_from: date, publish_to: date) -> pd.DataFrame:
    """All WINDFOR forecast rows published between the two UTC dates (inclusive)."""
    rows: list[dict] = []
    with httpx.Client() as client:
        for lo, hi in _windows(publish_from, publish_to, CHUNK_DAYS):
            upper = datetime.combine(hi + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc)
            params = {
                "publishDateTimeFrom": datetime.combine(lo, datetime.min.time(), tzinfo=timezone.utc)
                .strftime("%Y-%m-%dT%H:%M:%SZ"),
                "publishDateTimeTo": upper.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "format": "json",
            }
            rows += _cached_fetch(client, "windfor", "/datasets/WINDFOR/stream", params)
    return parse_forecasts(rows)
