import asyncio
import json
import time
from collections import deque
from threading import Lock
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from src.pipelines.streaming_pipeline import (
    TransactionProducer,
    FraudPipelineConsumer,
    TRANSACTION_QUEUE,
)
from src.simulator.transaction_generator import TransactionGenerator
from src.utils.logging import logger


router = APIRouter()


# ══════════════════════════════════════════════════════════════════════════
# IN-MEMORY STORE  (thread-safe)
# Holds every processed result for the current server session.
# Swap for SQLite/Postgres if you want persistence across restarts.
# ══════════════════════════════════════════════════════════════════════════

class ResultStore:
    """
    Thread-safe in-memory store for processed transaction results.
    Keeps the last MAX_RESULTS results in a deque (auto-evicts oldest).
    """

    MAX_RESULTS = 5000

    def __init__(self):
        self._results: deque[dict] = deque(maxlen=self.MAX_RESULTS)
        self._lock = Lock()

        # SSE subscribers: list of asyncio.Queue, one per connected client
        self._subscribers: list[asyncio.Queue] = []
        self._sub_lock = Lock()

        # Track session start for "last 5 min" filter
        self._session_start = time.time()

    def add(self, result: dict):
        """Called by the consumer thread when a result is ready."""
        result["processed_at"] = time.time()
        with self._lock:
            self._results.append(result)
        # fan-out to all SSE subscribers
        with self._sub_lock:
            for q in self._subscribers:
                try:
                    q.put_nowait(result)
                except asyncio.QueueFull:
                    pass  # slow client — skip, don't block

    def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=200)
        with self._sub_lock:
            self._subscribers.append(q)
        return q

    def unsubscribe(self, q: asyncio.Queue):
        with self._sub_lock:
            try:
                self._subscribers.remove(q)
            except ValueError:
                pass

    def all_results(self) -> list[dict]:
        with self._lock:
            return list(self._results)

    def reset(self):
        with self._lock:
            self._results.clear()
        self._session_start = time.time()


store = ResultStore()


# ══════════════════════════════════════════════════════════════════════════
# PIPELINE SINGLETON
# Consumer starts once at module load; stays alive for the server lifetime.
# ══════════════════════════════════════════════════════════════════════════

_consumer = FraudPipelineConsumer(result_callback=store.add)
_consumer.start()

_producer: TransactionProducer | None = None


def _get_producer() -> TransactionProducer:
    global _producer
    if _producer is None:
        _producer = TransactionProducer()
    return _producer


# ══════════════════════════════════════════════════════════════════════════
# REQUEST / RESPONSE MODELS
# ══════════════════════════════════════════════════════════════════════════

class SimulateRequest(BaseModel):
    mode: str = "normal"             # normal | stolen_card | geo_attack | velocity_burst
    num_transactions: int = 10       # 1 – 500


class SimulateResponse(BaseModel):
    queued: int
    mode: str
    transactions: list[dict]         # raw generated transactions (before prediction)


# ══════════════════════════════════════════════════════════════════════════
# ROUTES
# ══════════════════════════════════════════════════════════════════════════

@router.get("/health")
def health():
    return {
        "status": "ok",
        "queue_size": TRANSACTION_QUEUE.qsize(),
        "results_stored": len(store.all_results()),
    }


# ── 1. Simulate ────────────────────────────────────────────────────────────

@router.post("/simulate", response_model=SimulateResponse)
def simulate(req: SimulateRequest):
    """
    Generate transactions and push them onto the prediction queue.

    Returns the raw generated transactions immediately so the frontend
    can show the user what was generated BEFORE predictions arrive.
    Predictions stream in via GET /simulate/stream.
    """
    if req.num_transactions < 1 or req.num_transactions > 500:
        raise HTTPException(
            status_code=422,
            detail="num_transactions must be between 1 and 500.",
        )

    valid_modes = {"normal", "stolen_card", "geo_attack", "velocity_burst"}
    if req.mode not in valid_modes:
        raise HTTPException(
            status_code=422,
            detail=f"mode must be one of {sorted(valid_modes)}.",
        )

    logger.info(f"POST /simulate  mode={req.mode}  n={req.num_transactions}")

    # Generate the batch
    generator = TransactionGenerator("transactions_data")
    transactions = generator.generate_transactions(
        req.num_transactions, req.mode
    )

    # Push onto the queue for async prediction
    for txn in transactions:
        TRANSACTION_QUEUE.put(txn)

    logger.info(f"{req.num_transactions} transactions queued for prediction.")

    # Return the raw transactions immediately (JSON-safe — strip ObjectId etc.)
    safe_transactions = [
        {k: str(v) if not isinstance(v, (int, float, str, bool, type(None))) else v
         for k, v in txn.items()}
        for txn in transactions
    ]

    return SimulateResponse(
        queued=req.num_transactions,
        mode=req.mode,
        transactions=safe_transactions,
    )


# ── 2. SSE results stream ──────────────────────────────────────────────────

@router.get("/simulate/stream")
async def simulate_stream():
    """
    Server-Sent Events endpoint.
    Each prediction result is pushed to the client as it completes.

    Frontend usage:
        const es = new EventSource('/simulate/stream');
        es.onmessage = (e) => {
            const result = JSON.parse(e.data);
            // update live feed table + stat cards
        };
    """
    q = store.subscribe()

    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            # Send a heartbeat immediately so the browser knows the connection is alive
            yield "data: {\"type\": \"connected\"}\n\n"

            while True:
                try:
                    # Wait up to 30 s for the next result
                    result = await asyncio.wait_for(q.get(), timeout=30.0)

                    # Make result JSON-safe
                    safe = _make_json_safe(result)
                    safe["type"] = "result"

                    yield f"data: {json.dumps(safe)}\n\n"

                except asyncio.TimeoutError:
                    # Send keepalive comment so connection stays open
                    yield ": keepalive\n\n"

        except asyncio.CancelledError:
            pass
        finally:
            store.unsubscribe(q)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",   # disable nginx buffering
        },
    )


# ── 3. Dashboard stats ─────────────────────────────────────────────────────

@router.get("/dashboard/stats")
def dashboard_stats():
    """
    Aggregate metrics for the four stat cards on the dashboard.

    Returns
    -------
    {
        total_transactions : int,
        fraud_rate_pct     : float,   e.g. 34.2
        blocked_count      : int,
        approved_count     : int,
        avg_latency_ms     : float,
        p99_latency_ms     : float,
        fraud_rate_vs_normal_pct : float   (difference vs baseline 5%)
    }
    """
    results = store.all_results()

    if not results:
        return _empty_stats()

    total    = len(results)
    blocked  = [r for r in results if r["decision"] == "BLOCKED"]
    approved = [r for r in results if r["decision"] == "APPROVED"]

    fraud_rate = round(len(blocked) / total * 100, 1)

    latencies  = [r["latency_ms"] for r in results]
    avg_lat    = round(sum(latencies) / len(latencies), 1)
    sorted_lat = sorted(latencies)
    p99_lat    = round(sorted_lat[max(0, int(len(sorted_lat) * 0.99) - 1)], 1)

    # Baseline fraud rate for normal mode ≈ 5%
    NORMAL_BASELINE_PCT = 5.0
    fraud_vs_normal = round(fraud_rate - NORMAL_BASELINE_PCT, 1)

    # Mode breakdown
    mode_counts: dict[str, int] = {}
    for r in results:
        m = r.get("simulation_mode", "unknown")
        mode_counts[m] = mode_counts.get(m, 0) + 1

    # Category breakdown (top 5)
    cat_counts: dict[str, int] = {}
    for r in results:
        cat = r.get("transaction", {}).get("category", "unknown")
        cat_counts[cat] = cat_counts.get(cat, 0) + 1
    top_categories = sorted(cat_counts.items(), key=lambda x: x[1], reverse=True)[:5]

    return {
        "total_transactions":      total,
        "fraud_rate_pct":          fraud_rate,
        "blocked_count":           len(blocked),
        "approved_count":          len(approved),
        "avg_latency_ms":          avg_lat,
        "p99_latency_ms":          p99_lat,
        "fraud_rate_vs_normal_pct": fraud_vs_normal,
        "mode_breakdown":          mode_counts,
        "top_categories":          dict(top_categories),
    }


def _empty_stats() -> dict:
    return {
        "total_transactions":      0,
        "fraud_rate_pct":          0.0,
        "blocked_count":           0,
        "approved_count":          0,
        "avg_latency_ms":          0.0,
        "p99_latency_ms":          0.0,
        "fraud_rate_vs_normal_pct": 0.0,
        "mode_breakdown":          {},
        "top_categories":          {},
    }


# ── 4. Live feed ───────────────────────────────────────────────────────────

@router.get("/dashboard/feed")
def dashboard_feed(limit: int = 50):
    """
    Last `limit` processed results for the live feed table.
    Most recent first.

    Each item contains:
        time, amount, category, score, mode, decision
    """
    if limit < 1 or limit > 500:
        limit = 50

    results = store.all_results()
    recent  = list(reversed(results))[:limit]

    feed = []
    for r in recent:
        txn = r.get("transaction", {})
        feed.append({
            "transaction_id":    r.get("transaction_id", ""),
            "time":              txn.get("transaction_time", ""),
            "amount":            txn.get("transaction_amount", 0),
            "category":          txn.get("category", ""),
            "fraud_probability": r.get("fraud_probability", 0),
            "simulation_mode":   r.get("simulation_mode", ""),
            "decision":          r.get("decision", ""),
            "latency_ms":        r.get("latency_ms", 0),
        })

    return {"count": len(feed), "feed": feed}


# ── 5. Fraud alerts ────────────────────────────────────────────────────────

@router.get("/dashboard/alerts")
def dashboard_alerts(limit: int = 20):
    """
    Most recent BLOCKED transactions with LLM reasoning.
    Used for the fraud alerts panel on the dashboard.

    Each item contains:
        transaction_id, amount, category, fraud_probability,
        simulation_mode, reasoning, latency_ms
    """
    if limit < 1 or limit > 200:
        limit = 20

    results = store.all_results()
    blocked = [r for r in reversed(results) if r["decision"] == "BLOCKED"][:limit]

    alerts = []
    for r in blocked:
        txn = r.get("transaction", {})
        alerts.append({
            "transaction_id":    r.get("transaction_id", ""),
            "time":              txn.get("transaction_time", ""),
            "amount":            txn.get("transaction_amount", 0),
            "category":          txn.get("category", ""),
            "fraud_probability": r.get("fraud_probability", 0),
            "simulation_mode":   r.get("simulation_mode", ""),
            "reasoning":         r.get("reasoning", ""),
            "latency_ms":        r.get("latency_ms", 0),
        })

    return {"count": len(alerts), "alerts": alerts}


# ── 6. Reset store (useful between demo runs) ──────────────────────────────

@router.post("/dashboard/reset")
def dashboard_reset():
    """Clear all stored results. Use between demo sessions."""
    store.reset()
    logger.info("Result store reset.")
    return {"status": "reset", "message": "All results cleared."}


# ══════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════

def _make_json_safe(obj):
    """Recursively convert non-JSON-serialisable values to strings."""
    if isinstance(obj, dict):
        return {k: _make_json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_make_json_safe(v) for v in obj]
    if isinstance(obj, (int, float, bool, str, type(None))):
        return obj
    return str(obj)