"""Forecast/actual alignment and error metrics.

Decision-time rule (no look-ahead): for a delivery interval starting at T and a
forecast horizon of H hours, the decision cutoff is T - H. Only forecasts with
publishTime <= cutoff are eligible, and the latest eligible one is used.
"""
from __future__ import annotations

import math

import pandas as pd

INTERVAL = pd.Timedelta("30min")
# MAPE is undefined at zero and explodes near zero, so it is computed only on
# intervals with actual generation at or above this level.
MAPE_MIN_ACTUAL_MW = 100.0


def select_forecasts(forecasts: pd.DataFrame, horizon_hours: float) -> pd.DataFrame:
    """Latest forecast per target interval with publish <= start - horizon."""
    cutoff = forecasts["start"] - pd.Timedelta(f"{horizon_hours}h")
    eligible = forecasts[forecasts["publish"] <= cutoff]
    chosen = eligible.sort_values("publish").groupby("start", as_index=False).last()
    return chosen.rename(columns={"publish": "forecast_publish"})[["start", "forecast_publish", "forecast"]]


def align(actuals: pd.DataFrame, forecasts: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp,
          horizon_hours: float) -> pd.DataFrame:
    """One row per 30-min interval in [start, end) with actual, forecast and error (forecast - actual).

    Intervals missing either value keep NaN so gaps are visible rather than interpolated.
    """
    grid = pd.DataFrame({"start": pd.date_range(start, end, freq=INTERVAL, inclusive="left", tz="UTC")})
    chosen = select_forecasts(forecasts, horizon_hours)
    df = grid.merge(actuals[["start", "actual"]], on="start", how="left").merge(chosen, on="start", how="left")
    df["error"] = df["forecast"] - df["actual"]
    return df


def compute_metrics(df: pd.DataFrame) -> dict:
    """MAE, RMSE, signed bias (forecast - actual, MW) and MAPE (%) over intervals with both values."""
    both = df.dropna(subset=["actual", "forecast"])
    n = len(both)
    result = {
        "expected_intervals": int(len(df)),
        "actual_intervals": int(df["actual"].notna().sum()),
        "forecast_intervals": int(df["forecast"].notna().sum()),
        "evaluated_intervals": int(n),
        "mae_mw": None, "rmse_mw": None, "bias_mw": None, "mape_pct": None,
        "mape_intervals": 0, "mape_min_actual_mw": MAPE_MIN_ACTUAL_MW,
    }
    if n == 0:
        return result
    err = both["forecast"] - both["actual"]
    result["mae_mw"] = float(err.abs().mean())
    result["rmse_mw"] = float(math.sqrt((err ** 2).mean()))
    result["bias_mw"] = float(err.mean())
    valid = both[both["actual"] >= MAPE_MIN_ACTUAL_MW]
    if len(valid):
        result["mape_pct"] = float(((valid["forecast"] - valid["actual"]).abs() / valid["actual"]).mean() * 100)
        result["mape_intervals"] = int(len(valid))
    return result
