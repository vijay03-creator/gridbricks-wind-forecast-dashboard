import pandas as pd
import pytest

from app.elexon import ElexonError, _windows, parse_actuals, parse_forecasts
from datetime import date


def test_parse_actuals_filters_wind_dedupes_and_keeps_latest_revision():
    rows = [
        {"fuelType": "WIND", "startTime": "2026-01-01T00:00:00Z", "publishTime": "2026-01-01T00:30:00Z", "generation": 1000},
        {"fuelType": "WIND", "startTime": "2026-01-01T00:00:00Z", "publishTime": "2026-01-01T01:00:00Z", "generation": 1010},
        {"fuelType": "CCGT", "startTime": "2026-01-01T00:00:00Z", "publishTime": "2026-01-01T00:30:00Z", "generation": 9999},
        {"fuelType": "WIND", "startTime": "2026-01-01T00:30:00Z", "publishTime": "2026-01-01T01:00:00Z", "generation": None},
    ]
    df = parse_actuals(rows)
    assert len(df) == 1
    assert df.iloc[0]["actual"] == 1010
    assert str(df["start"].dt.tz) == "UTC"


def test_parse_actuals_missing_field_raises():
    with pytest.raises(ElexonError):
        parse_actuals([{"startTime": "2026-01-01T00:00:00Z"}])


def test_parse_forecasts_dedupes_and_converts_to_utc():
    rows = [
        {"startTime": "2026-01-02T00:00:00Z", "publishTime": "2026-01-01T10:00:00Z", "generation": 1.0},
        {"startTime": "2026-01-02T00:00:00Z", "publishTime": "2026-01-01T10:00:00Z", "generation": 2.0},
        {"startTime": "2026-01-02T01:00:00+01:00", "publishTime": "2026-01-01T11:00:00Z", "generation": 3.0},
    ]
    df = parse_forecasts(rows)
    assert len(df) == 2  # exact (start, publish) duplicate collapsed, later one kept
    assert df.iloc[0]["forecast"] == 2.0
    assert df.iloc[1]["forecast"] == 3.0
    assert df.iloc[1]["start"] == pd.Timestamp("2026-01-02T00:00:00Z")  # 01:00+01:00 normalised to UTC


def test_parse_forecasts_missing_field_raises():
    with pytest.raises(ElexonError):
        parse_forecasts([{"startTime": "2026-01-02T00:00:00Z", "generation": 1.0}])


def test_windows_cover_range_without_overlap():
    wins = list(_windows(date(2026, 1, 1), date(2026, 1, 31), 7))
    assert wins[0][0] == date(2026, 1, 1) and wins[-1][1] == date(2026, 1, 31)
    for (_, hi), (lo, _) in zip(wins, wins[1:]):
        assert (lo - hi).days == 1
