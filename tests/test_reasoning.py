"""Tests for FraudReasoningAI formatting helpers.

These test the pure formatting logic without making any LLM/Groq network call.
Constructing the object would require a GROQ_API_KEY, so we use __new__ and
only exercise the private formatting methods.
"""

import pytest

from src.inference.reasoning import FraudReasoningAI


def make_reasoner():
    return FraudReasoningAI.__new__(FraudReasoningAI)


def test_format_transaction_strips_simulator_and_internal_keys():
    reasoner = make_reasoner()
    txn = {
        "id": "abc",
        "_id": "internal-id",
        "simulation_mode": "stolen_card",
        "transaction_amount": 500.0,
        "category": "grocery_pos",
    }
    out = reasoner._format_transaction(txn)
    assert "simulation_mode" not in out
    assert "123" not in "".join(out.split())
    assert "transaction_amount" in out
    assert "grocery_pos" in out
    assert "<_id" not in out


def test_format_transaction_empty():
    reasoner = make_reasoner()
    assert reasoner._format_transaction({}) == "(no transaction data)"


def test_format_reasoning_transaction_keeps_model_features_only():
    reasoner = make_reasoner()
    out = reasoner._format_reasoning_transaction(
        {
            "transaction_amount": 500.0,
            "category": "grocery_pos",
            "transaction_hour": 2,
            "buyer_age": 66,
            "distance_km": 100.0,
            "is_night_transaction": 1,
            "buyer_gender": "F",
            "credit_card_number": "secret",
        }
    )
    assert "transaction_amount" in out
    assert "credit_card_number" not in out


def test_format_transaction_only_skipped_keys():
    reasoner = make_reasoner()
    out = reasoner._format_transaction({"simulation_mode": "normal", "id": "x"})
    assert out == "(no transaction data)"


def test_format_prediction():
    reasoner = make_reasoner()
    pred = {
        "decision": "BLOCKED",
        "fraud_probability": 0.943,
        "threshold": 0.50,
    }
    out = reasoner._format_prediction(pred)
    assert "BLOCKED" in out
    assert "94.3%" in out
    assert "0.5" in out


def test_format_prediction_defaults():
    reasoner = make_reasoner()
    out = reasoner._format_prediction({})
    assert "UNKNOWN" in out


def test_fallback_reasoning_is_visible_for_blocked_transaction():
    reasoner = make_reasoner()
    out = reasoner._fallback_reasoning(
        {
            "transaction_amount": 900.0,
            "transaction_hour": 2,
            "is_night_transaction": 1,
        },
        {"fraud_probability": 0.994},
    )
    assert "blocked" in out
    assert "99.4%" in out
    assert "late-night activity" in out
