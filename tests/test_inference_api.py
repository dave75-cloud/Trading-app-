from fastapi.testclient import TestClient

from services.inference_api import main as api


def _client(tmp_path, monkeypatch) -> TestClient:
    """Return a client bound to an isolated sqlite DB."""
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.delenv("DB_URL", raising=False)
    api._store.cache_clear()
    return TestClient(api.app)


def test_health_ok(tmp_path, monkeypatch):
    c = _client(tmp_path, monkeypatch)
    r = c.get("/health")
    assert r.status_code == 200
    j = r.json()
    assert j["status"] == "ok"


def test_latest_signal_contract(tmp_path, monkeypatch):
    c = _client(tmp_path, monkeypatch)
    r = c.get("/signals/latest", params={"h": "30m"})
    assert r.status_code == 200
    j = r.json()
    assert "now" in j
    assert "horizon" in j


def test_backtest_runs_and_returns_summary(tmp_path, monkeypatch):
    c = _client(tmp_path, monkeypatch)
    r = c.post("/backtest/run", json={"horizon": "30m", "days": 30})
    assert r.status_code == 200
    j = r.json()
    assert "summary" in j
    assert "trades" in j["summary"]
    assert "pnl" in j["summary"]


def test_signal_history_and_evaluate_work(tmp_path, monkeypatch):
    c = _client(tmp_path, monkeypatch)
    for _ in range(3):
        r = c.get("/signals/latest", params={"h": "30m"})
        assert r.status_code == 200

    rh = c.get("/signals/history", params={"days": 7, "h": "30m", "limit": 50})
    assert rh.status_code == 200
    jh = rh.json()
    assert jh["count"] >= 1
    assert len(jh["rows"]) == jh["count"]

    re = c.get("/signals/evaluate", params={"days": 7, "h": "30m", "limit": 50})
    assert re.status_code == 200
    je = re.json()
    assert "summary" in je
    assert "count" in je["summary"]
