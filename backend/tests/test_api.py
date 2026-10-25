import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app import main


def ts(s):
    return pd.Timestamp(s, tz="UTC")


@pytest.fixture()
def client(monkeypatch):
    actuals = pd.DataFrame({"start": [ts("2026-01-05 00:00"), ts("2026-01-05 00:30")], "actual": [1000.0, 2000.0]})
    forecasts = pd.DataFrame({
        "start": [ts("2026-01-05 00:00"), ts("2026-01-05 00:30"), ts("2026-01-05 00:30")],
        "publish": [ts("2026-01-03 00:00"), ts("2026-01-03 00:00"), ts("2026-01-04 23:00")],  # last one leaks at 24h
        "forecast": [1100.0, 1500.0, 1999.0],
    })
    monkeypatch.setattr(main, "load_data", lambda: (actuals, forecasts))
    return TestClient(main.app)


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_metrics_respect_cutoff(client):
    r = client.get("/api/metrics", params={"start": "2026-01-05", "end": "2026-01-05", "horizon_hours": 24})
    body = r.json()
    assert r.status_code == 200
    assert body["expected_intervals"] == 48
    assert body["evaluated_intervals"] == 2
    assert body["mae_mw"] == pytest.approx((100 + 500) / 2)  # 1999 forecast not used at 24h horizon
    assert body["bias_mw"] == pytest.approx((100 - 500) / 2)


def test_series_points(client):
    r = client.get("/api/series", params={"start": "2026-01-05", "end": "2026-01-05"})
    pts = r.json()["points"]
    assert len(pts) == 48
    assert pts[0]["t"] == "2026-01-05T00:00:00Z" and pts[0]["error"] == 100.0
    assert pts[2]["actual"] is None and pts[2]["forecast"] is None


def test_rejects_out_of_range_and_reversed_dates(client):
    assert client.get("/api/metrics", params={"start": "2025-12-31"}).status_code == 422
    assert client.get("/api/metrics", params={"start": "2026-01-10", "end": "2026-01-09"}).status_code == 422
    assert client.get("/api/metrics", params={"horizon_hours": 9999}).status_code == 422


def test_upstream_failure_returns_502(monkeypatch):
    def boom():
        raise main.elexon.ElexonError("down")

    monkeypatch.setattr(main, "load_data", boom)
    assert TestClient(main.app).get("/api/metrics").status_code == 502
