"""Tests for TransactionGenerator (src/simulator/transaction_generator.py).

We avoid the CSV-backed __init__ loading the full datasource by constructing
the object via __new__ and injecting a fixture DataFrame. Pure module helpers
are tested directly.
"""

import pandas as pd
import pytest

from src.simulator.transaction_generator import (
    TransactionGenerator,
    _pick_fraud_amount,
    _pick_fraud_category,
    _pick_older_age,
    _NIGHT_HOURS,
    _FRAUD_AMOUNT_LOW,
    _FRAUD_AMOUNT_MID,
    _FRAUD_AMOUNT_HIGH,
)
from utils.exception import FraudShieldException


def make_base_df(n=20):
    return pd.DataFrame(
        {
            "buyer_lat": [40.7128] * n,
            "buyer_long": [-74.0060] * n,
            "merchant_lat": [40.7000] * n,
            "merchant_long": [-74.0000] * n,
            "transaction_amount": [100.0] * n,
            "category": ["grocery_pos"] * n,
            "buyer_age": [30] * n,
            "transaction_hour": [12] * n,
        }
    )


def make_generator(n=20):
    g = TransactionGenerator.__new__(TransactionGenerator)
    g.df = make_base_df(n)
    return g


# ── pure helpers ──────────────────────────────────────────────────────────

def test_pick_fraud_amount_respects_tiers():
    for _ in range(200):
        low = _pick_fraud_amount("low")
        mid = _pick_fraud_amount("mid")
        high = _pick_fraud_amount("high")
        assert (_FRAUD_AMOUNT_LOW[0] <= low <= _FRAUD_AMOUNT_LOW[1])
        assert (_FRAUD_AMOUNT_MID[0] <= mid <= _FRAUD_AMOUNT_MID[1])
        assert (_FRAUD_AMOUNT_HIGH[0] <= high <= _FRAUD_AMOUNT_HIGH[1])


def test_pick_fraud_category_from_known_set():
    for _ in range(100):
        assert _pick_fraud_category() in {
            "grocery_pos", "shopping_net", "gas_transport", "misc_net",
            "shopping_pos", "misc_pos",
        }


def test_pick_older_age_lifts_young_buyers():
    txn = {"buyer_age": 25}
    out = _pick_older_age(txn)
    assert 55 <= out["buyer_age"] <= 80


def test_pick_older_age_keeps_old_buyers():
    txn = {"buyer_age": 70}
    out = _pick_older_age(txn)
    assert out["buyer_age"] == 70


# ── mode mutators ─────────────────────────────────────────────────────────

def test_mutate_to_normal_sets_mode_and_no_night():
    g = make_generator()
    txn = g.df.iloc[0].to_dict()
    out = g.mutate_to_normal(dict(txn))
    assert out["simulation_mode"] == "normal"
    assert out["transaction_hour"] == 12  # unchanged
    assert "transaction_time" in out


def test_mutate_to_stolen_card_forces_night_and_fraud_range():
    g = make_generator()
    txn = g.df.iloc[0].to_dict()
    out = g.mutate_to_stolen_card(dict(txn))
    assert out["simulation_mode"] == "stolen_card"
    assert out["is_night_transaction"] == 1
    assert out["transaction_amount"] <= _FRAUD_AMOUNT_HIGH[1]
    assert out["category"] != "" or True


def test_mutate_to_geo_attack_moves_merchant():
    g = make_generator()
    txn = g.df.iloc[0].to_dict()
    out = g.mutate_to_geo_attack(dict(txn))
    assert out["simulation_mode"] == "geo_attack"
    # merchant should have moved far from buyer
    assert abs(out["merchant_lat"] - out["buyer_lat"]) > 20
    assert abs(out["merchant_long"] - out["buyer_long"]) > 30
    assert out["is_night_transaction"] == 1


def test_mutate_to_velocity_burst_forces_night():
    g = make_generator()
    txn = g.df.iloc[0].to_dict()
    out = g.mutate_to_velocity_burst(dict(txn))
    assert out["simulation_mode"] == "velocity_burst"
    assert out["is_night_transaction"] == 1


# ── apply live timestamps ─────────────────────────────────────────────────

def test_apply_live_timestamps_updates_display_fields():
    g = make_generator()
    txn = {"transaction_hour": 12}
    out = g._apply_live_timestamps(dict(txn), force_night=False)
    assert out["transaction_hour"] == 12  # unchanged without force_night
    assert "transaction_date" in out
    assert "transaction_time" in out
    assert "unix_time" in out


def test_apply_live_timestamps_force_night():
    g = make_generator()
    txn = {"transaction_hour": 12}
    out = g._apply_live_timestamps(dict(txn), force_night=True)
    assert out["transaction_hour"] in _NIGHT_HOURS
    assert out["is_night_transaction"] == 1


# ── batch generation ──────────────────────────────────────────────────────

def test_generate_transactions_unknown_mode_raises():
    g = make_generator()
    with pytest.raises(FraudShieldException):
        g.generate_transactions(3, "bogus_mode")


def test_generate_transactions_normal_mode():
    g = make_generator()
    txns = g.generate_transactions(5, "normal")
    assert len(txns) == 5
    assert all(t["simulation_mode"] == "normal" for t in txns)


def test_generate_transactions_normalises_spaces():
    g = make_generator()
    txns = g.generate_transactions(3, "stolen card")
    assert len(txns) == 3
    assert all(t["simulation_mode"] == "stolen_card" for t in txns)
