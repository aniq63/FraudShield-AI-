"""Tests for the streaming pipeline consumer (src/pipelines/streaming_pipeline.py).

We avoid the real FraudPredictor/FraudReasoningAI (they load from S3 and call
Groq). Instead we build a FraudPipelineConsumer via __new__ and inject fakes,
so we can verify the per-transaction orchestration logic.
"""

import pytest

from src.pipelines.streaming_pipeline import FraudPipelineConsumer


def make_consumer(predictor, reasoner):
    c = FraudPipelineConsumer.__new__(FraudPipelineConsumer)
    c.predictor = predictor
    c.reasoner = reasoner
    return c


class FakePredictor:
    def __init__(self, decision="BLOCKED", prob=0.9):
        self._decision = decision
        self._prob = prob

    def predict(self, txn):
        return {
            "transaction_id": str(txn.get("id", "")),
            "fraud_probability": self._prob,
            "decision": self._decision,
            "threshold": 0.5,
            "raw_transaction": txn,
        }


class FakeReasoner:
    def __init__(self, output="Reasoning text"):
        self.output = output
        self.calls = 0

    def explain(self, txn, pred):
        self.calls += 1
        return self.output


def sample_txn(**overrides):
    txn = {
        "id": "txn-1",
        "simulation_mode": "stolen_card",
        "transaction_amount": 500.0,
        "category": "grocery_pos",
    }
    txn.update(overrides)
    return txn


def test_process_blocked_triggers_reasoning():
    predictor = FakePredictor("BLOCKED", 0.9)
    reasoner = FakeReasoner("High risk account.")
    consumer = make_consumer(predictor, reasoner)

    result = consumer._process(sample_txn())
    assert result["decision"] == "BLOCKED"
    assert result["fraud_probability"] == 0.9
    assert result["reasoning"] == "High risk account."
    assert result["simulation_mode"] == "stolen_card"
    assert "latency_ms" in result
    assert "transaction" in result
    assert reasoner.calls == 1


def test_process_approved_skips_reasoning():
    predictor = FakePredictor("APPROVED", 0.05)
    reasoner = FakeReasoner("should not be called")
    consumer = make_consumer(predictor, reasoner)

    result = consumer._process(sample_txn())
    assert result["decision"] == "APPROVED"
    assert result["reasoning"] is None
    assert reasoner.calls == 0


def test_process_reasoning_failure_falls_back():
    predictor = FakePredictor("BLOCKED", 0.9)

    class FailingReasoner:
        def explain(self, txn, pred):
            raise RuntimeError("groq down")

    consumer = make_consumer(predictor, FailingReasoner())
    result = consumer._process(sample_txn())
    assert result["reasoning"] == "Reasoning unavailable."
