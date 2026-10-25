import math

import pandas as pd
import pytest

from app.analysis import MAPE_MIN_ACTUAL_MW, align, compute_metrics, select_forecasts


def ts(s: str) -> pd.Timestamp:
    return pd.Timestamp(s, tz="UTC")


def fc(rows):
    return pd.DataFrame(
        [{"start": ts(s), "publish": ts(p), "forecast": g} for s, p, g in rows]
    )


def test_cutoff_selects_latest_forecast_not_after_cutoff():
    forecasts = fc([
        ("2026-01-02 12:00", "2026-01-01 06:00", 100.0),  # old
        ("2026-01-02 12:00", "2026-01-01 11:00", 200.0),  # latest before cutoff (12:00 - 24h = 01-01 12:00)
        ("2026-01-02 12:00", "2026-01-01 12:00", 300.0),  # exactly at cutoff -> eligible and latest
        ("2026-01-02 12:00", "2026-01-01 12:30", 999.0),  # after cutoff -> leakage, must be ignored
    ])
    out = select_forecasts(forecasts, horizon_hours=24)
    assert len(out) == 1
    assert out.iloc[0]["forecast"] == 300.0
    assert out.iloc[0]["forecast_publish"] == ts("2026-01-01 12:00")


def test_no_eligible_forecast_means_no_row():
    forecasts = fc([("2026-01-02 12:00", "2026-01-02 06:00", 500.0)])
    assert select_forecasts(forecasts, horizon_hours=24).empty


def test_shorter_horizon_allows_fresher_forecast():
    forecasts = fc([
        ("2026-01-02 12:00", "2026-01-01 10:00", 100.0),
        ("2026-01-02 12:00", "2026-01-02 06:00", 250.0),
    ])
    assert select_forecasts(forecasts, 24).iloc[0]["forecast"] == 100.0
    assert select_forecasts(forecasts, 6).iloc[0]["forecast"] == 250.0


def test_align_builds_full_grid_and_keeps_gaps():
    actuals = pd.DataFrame({"start": [ts("2026-01-01 00:00"), ts("2026-01-01 01:00")], "actual": [1000.0, 800.0]})
    forecasts = fc([
        ("2026-01-01 00:00", "2025-12-31 00:00", 900.0),
        ("2026-01-01 00:30", "2025-12-31 00:00", 700.0),  # actual missing for this interval
    ])
    df = align(actuals, forecasts, ts("2026-01-01 00:00"), ts("2026-01-01 01:30"), horizon_hours=24)
    assert list(df["start"]) == [ts("2026-01-01 00:00"), ts("2026-01-01 00:30"), ts("2026-01-01 01:00")]
    assert df.loc[0, "error"] == -100.0  # forecast - actual
    assert math.isnan(df.loc[1, "actual"]) and df.loc[1, "forecast"] == 700.0
    assert math.isnan(df.loc[2, "forecast"]) and df.loc[2, "actual"] == 800.0
    assert math.isnan(df.loc[1, "error"]) and math.isnan(df.loc[2, "error"])


def test_metrics_values():
    df = pd.DataFrame({
        "actual": [1000.0, 2000.0, 500.0, None],
        "forecast": [1100.0, 1800.0, 500.0, 300.0],
    })
    df["error"] = df["forecast"] - df["actual"]
    m = compute_metrics(df)
    assert m["expected_intervals"] == 4
    assert m["evaluated_intervals"] == 3
    assert m["mae_mw"] == pytest.approx((100 + 200 + 0) / 3)
    assert m["rmse_mw"] == pytest.approx(math.sqrt((100**2 + 200**2 + 0) / 3))
    assert m["bias_mw"] == pytest.approx((100 - 200 + 0) / 3)
    assert m["mape_pct"] == pytest.approx((0.1 + 0.1 + 0.0) / 3 * 100)
    assert m["mape_intervals"] == 3


def test_mape_excludes_near_zero_actuals():
    df = pd.DataFrame({"actual": [0.0, MAPE_MIN_ACTUAL_MW - 1, 1000.0], "forecast": [50.0, 80.0, 900.0]})
    m = compute_metrics(df)
    assert m["evaluated_intervals"] == 3
    assert m["mape_intervals"] == 1
    assert m["mape_pct"] == pytest.approx(10.0)


def test_metrics_empty():
    m = compute_metrics(pd.DataFrame({"actual": [None], "forecast": [None]}))
    assert m["evaluated_intervals"] == 0
    assert m["mae_mw"] is None and m["mape_pct"] is None
