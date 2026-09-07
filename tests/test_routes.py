"""Tests for the FastAPI routes (api/routes.py).

api/routes.py starts a FraudPipelineConsumer singleton at import time, which
would normally load models from S3. To test the pure logic (ResultStore,
dashboard aggregation, JSON-safety) offline, we patch the streaming-pipeline
classes before importing the routes module.
"""

import json
from collections import deque

import pytest

from tests.conftest import FakeConsumer  # noqa: F401  (re-export)


def _patch_consumer_and_import():
    """Swap FraudPipelineConsumer for a fake, then import api.routes."""
    import src.pipelines.streaming_pipeline as sp

    original = sp.FraudPipelineConsumer
    sp.FraudPipelineConsumer = FakeConsumer
    try:
        import api.routes as routes_mod
        return routes_mod
    finally:
        sp.FraudPipelineConsumer = original


@pytest.fixture(scope="module")
def routes():
    return _patch_consumer_and_import()


# ──────────────────────────────────────────────────────────────────────────
# ResultStore
# ──────────────────────────────────────────────────────────────────────────

def test_result_store_add_and_all(routes):
    store = routes.ResultStore()
    store.add({"decision": "BLOCKED", "latency_ms": 10})
    results = store.all_results()
    assert len(results) == 1
    assert "processed_at" in results[0]


def test_result_store_reset(routes):
    store = routes.ResultStore()
    store.add({"decision": "BLOCKED"})
    store.reset()
    assert store.all_results() == []


def test_result_store_evicts_oldest(routes):
    store = routes.ResultStore()
    store._results = deque(maxlen=3)
    for i in range(5):
        store.add({"i": i})
    results = store.all_results()
    assert len(results) == 3
    assert results[0]["i"] == 2
    assert results[-1]["i"] == 4


def test_result_store_subscribe_fanout(routes):
    store = routes.ResultStore()
    q = store.subscribe()
    store.add({"decision": "BLOCKED"})
    item = q.get_nowait()
    assert item["decision"] == "BLOCKED"
    store.unsubscribe(q)


# ──────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────

def test_make_json_safe(routes):
    obj = {"a": 1, "b": "x", "c": {"d": object(), "e": [1, None, True]}}
    safe = routes._make_json_safe(obj)
    assert isinstance(safe["c"]["d"], str)
    json.dumps(safe)  # must be serialisable


# ──────────────────────────────────────────────────────────────────────────
# Dashboard aggregation functions
# ──────────────────────────────────────────────────────────────────────────

def make_result(decision, latency, mode, category):
    return {
        "decision": decision,
        "latency_ms": latency,
        "simulation_mode": mode,
        "transaction": {"category": category},
    }


def test_empty_stats(routes):
    stats = routes._empty_stats()
    assert stats["total_transactions"] == 0
    assert stats["fraud_rate_pct"] == 0.0


def test_dashboard_stats_aggregation(routes, monkeypatch):
    store = routes.ResultStore()
    for r in [
        make_result("BLOCKED", 10, "stolen_card", "grocery_pos"),
        make_result("BLOCKED", 20, "geo_attack", "grocery_pos"),
        make_result("APPROVED", 30, "normal", "shopping_net"),
    ]:
        store.add(r)

    monkeypatch.setattr(routes, "store", store)
    stats = routes.dashboard_stats()
    assert stats["total_transactions"] == 3
    assert stats["blocked_count"] == 2
    assert stats["approved_count"] == 1
    assert stats["fraud_rate_pct"] == pytest.approx(66.7, abs=0.1)
    assert stats["avg_latency_ms"] == pytest.approx(20.0, abs=0.1)
    assert stats["top_categories"]["grocery_pos"] == 2
    assert stats["mode_breakdown"]["stolen_card"] == 1


def test_dashboard_feed_ordering(routes, monkeypatch):
    store = routes.ResultStore()
    store.add(make_result("BLOCKED", 10, "stolen_card", "grocery_pos"))
    store.add(make_result("APPROVED", 30, "normal", "shopping_net"))
    monkeypatch.setattr(routes, "store", store)

    feed = routes.dashboard_feed(limit=50)
    assert feed["count"] == 2
    # most recent first
    assert feed["feed"][0]["decision"] == "APPROVED"
    assert feed["feed"][1]["decision"] == "BLOCKED"
    assert feed["feed"][0]["amount"] == 0  # no amount in raw txn → default


def test_dashboard_alerts_only_blocked(routes, monkeypatch):
    store = routes.ResultStore()
    blocked = make_result("BLOCKED", 10, "stolen_card", "grocery_pos")
    blocked["reasoning"] = "High risk"
    store.add(blocked)
    store.add(make_result("APPROVED", 30, "normal", "shopping_net"))
    monkeypatch.setattr(routes, "store", store)

    alerts = routes.dashboard_alerts(limit=20)
    assert alerts["count"] == 1
    assert alerts["alerts"][0]["reasoning"] == "High risk"
