"""Tests for FraudPredictor preprocessing logic (src/inference/predictor.py).

The predictor's __init__ loads model + preprocessor from MLflow, which we do
not want to hit in unit tests. We construct instances via __new__ and install
a fake preprocessor that records the DataFrame it receives, so we can assert
on the preprocessing steps without a real fitted ColumnTransformer.
"""

import numpy as np
import pandas as pd
import pytest

from src.inference import predictor as pred_mod
from src.inference.predictor import FraudPredictor, _haversine, FRAUD_THRESHOLD


def make_instance(expected_columns):
    """Build a FraudPredictor without running the MLflow-loading __init__."""
    inst = FraudPredictor.__new__(FraudPredictor)
    inst._expected_columns = list(expected_columns)
    return inst


@pytest.fixture
def predictor():
    return make_instance(
        ["buyer_gender", "category", "distance_km", "transaction_amount_log",
         "is_night_transaction", "transaction_hour", "buyer_age"]
    )


def _transaction_dict(**overrides):
    txn = {
        "id": "txn-1",
        "simulation_mode": "stolen_card",
        "transaction_is_fraud": 0,
        "transaction_date": "2023-01-15",
        "buyer_date_of_birth": "1985-01-15",
        "buyer_lat": 40.7128,
        "buyer_long": -74.0060,
        "merchant_lat": 40.7000,
        "merchant_long": -74.0000,
        "transaction_amount": 500.0,
        "transaction_hour": 23,
        "merchant": "m1",
        "credit_card_number": "1111",
        "buyer_city": "NYC",
        "buyer_state": "NY",
        "buyer_zip": 11211,
        "buyer_city_pop": 1000,
        "unix_time": 1700000000,
        "buyer_job": "Engineer",
        "transaction_time": "23:00:00",
        "buyer_gender": "M",
        "category": "grocery_pos",
    }
    txn.update(overrides)
    return txn


def test_haversine_zero_distance():
    assert _haversine(np.array([40.0]), np.array([-74.0]),
                      np.array([40.0]), np.array([-74.0]))[0] == pytest.approx(0.0)


def test_haversine_known_distance():
    # London -> New York approx 5570 km
    d = _haversine(np.array([51.5074]), np.array([-0.1278]),
                   np.array([40.7128]), np.array([-74.0060]))[0]
    assert d == pytest.approx(5570, rel=0.05)


def test_preprocess_with_real_preprocessor():
    """End-to-end: _preprocess feeds a fitted ColumnTransformer correctly."""
    from sklearn.compose import ColumnTransformer
    from sklearn.preprocessing import StandardScaler, OneHotEncoder

    cat = ["buyer_gender", "category"]
    num = ["distance_km", "transaction_amount_log", "is_night_transaction",
           "transaction_hour", "buyer_age"]
    pre = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore"), cat),
            ("num", StandardScaler(), num),
        ]
    )
    # Fit on dummy data so feature_names_in_ is populated
    fit_df = pd.DataFrame(
        {
            "buyer_gender": ["M", "F"],
            "category": ["grocery_pos", "shopping_net"],
            "distance_km": [1.0, 2.0],
            "transaction_amount_log": [5.0, 6.0],
            "is_night_transaction": [1, 0],
            "transaction_hour": [23, 5],
            "buyer_age": [60, 40],
        }
    )
    pre.fit(fit_df)

    inst = make_instance(list(pre.feature_names_in_))
    inst.preprocessor = pre

    transaction = _transaction_dict()
    transaction.pop("transaction_date")
    transaction.pop("buyer_date_of_birth")
    X = inst._preprocess(pd.DataFrame([transaction]))
    # one row of features produced by preprocessor
    assert X.shape[0] == 1
    assert X.shape[1] == pre.transform(fit_df.head(1)).shape[1]


def test_align_columns_fills_missing_and_drops_extra(predictor, caplog):
    df = pd.DataFrame(
        {
            "buyer_gender": ["M"],
            "category": ["grocery_pos"],
            "distance_km": [1.0],
            "transaction_amount_log": [5.0],
            "is_night_transaction": [1],
            "transaction_hour": [23],
            "buyer_age": [60],
            "unexpected_col": [99],
        }
    )
    aligned = predictor._align_columns(df)
    # extra dropped, order matches expected
    assert list(aligned.columns) == predictor._expected_columns
    assert "unexpected_col" not in aligned.columns


def test_predict_returns_expected_structure():
    from sklearn.preprocessing import StandardScaler, OneHotEncoder
    from sklearn.compose import ColumnTransformer

    # Use a deterministic stub model + preprocessor to exercise predict()
    class StubModel:
        def predict_proba(self, X):
            return np.array([[0.3, 0.7]])

    cat = ["buyer_gender", "category"]
    num = ["distance_km", "transaction_amount_log", "is_night_transaction",
           "transaction_hour", "buyer_age"]
    pre = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore"), cat),
            ("num", StandardScaler(), num),
        ]
    )
    fit_df = pd.DataFrame(
        {
            "buyer_gender": ["M", "F"],
            "category": ["grocery_pos", "shopping_net"],
            "distance_km": [1.0, 2.0],
            "transaction_amount_log": [5.0, 6.0],
            "is_night_transaction": [1, 0],
            "transaction_hour": [23, 5],
            "buyer_age": [60, 40],
        }
    )
    pre.fit(fit_df)

    inst = make_instance(list(pre.feature_names_in_))
    inst.preprocessor = pre
    inst.model = StubModel()

    result = inst.predict(_transaction_dict())
    assert result["decision"] == "BLOCKED"  # 0.70 >= threshold
    assert result["fraud_probability"] == pytest.approx(0.7, abs=1e-4)
    assert result["threshold"] == FRAUD_THRESHOLD
    assert result["transaction_id"] == "txn-1"
    assert result["raw_transaction"]["simulation_mode"] == "stolen_card"


def test_predict_threshold_boundary():
    class StubModel:
        def predict_proba(self, X):
            return np.array([[0.0, FRAUD_THRESHOLD]])

    from sklearn.compose import ColumnTransformer
    from sklearn.preprocessing import StandardScaler, OneHotEncoder

    cat = ["buyer_gender", "category"]
    num = ["distance_km", "transaction_amount_log", "is_night_transaction",
           "transaction_hour", "buyer_age"]
    pre = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore"), cat),
            ("num", StandardScaler(), num),
        ]
    )
    fit_df = pd.DataFrame(
        {
            "buyer_gender": ["M", "F"],
            "category": ["grocery_pos", "shopping_net"],
            "distance_km": [1.0, 2.0],
            "transaction_amount_log": [5.0, 6.0],
            "is_night_transaction": [1, 0],
            "transaction_hour": [23, 5],
            "buyer_age": [60, 40],
        }
    )
    pre.fit(fit_df)
    inst = make_instance(list(pre.feature_names_in_))
    inst.preprocessor = pre
    inst.model = StubModel()

    # proba == threshold → exact boundary is BLOCKED (>= threshold)
    result = inst.predict(_transaction_dict())
    assert result["decision"] == "BLOCKED"
    assert result["fraud_probability"] == pytest.approx(FRAUD_THRESHOLD)


def test_predict_batch_returns_list():
    class StubModel:
        def predict_proba(self, X):
            return np.array([[0.1, 0.9]] * len(X))

    from sklearn.compose import ColumnTransformer
    from sklearn.preprocessing import StandardScaler, OneHotEncoder

    cat = ["buyer_gender", "category"]
    num = ["distance_km", "transaction_amount_log", "is_night_transaction",
           "transaction_hour", "buyer_age"]
    pre = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore"), cat),
            ("num", StandardScaler(), num),
        ]
    )
    fit_df = pd.DataFrame(
        {
            "buyer_gender": ["M", "F"],
            "category": ["grocery_pos", "shopping_net"],
            "distance_km": [1.0, 2.0],
            "transaction_amount_log": [5.0, 6.0],
            "is_night_transaction": [1, 0],
            "transaction_hour": [23, 5],
            "buyer_age": [60, 40],
        }
    )
    pre.fit(fit_df)
    inst = make_instance(list(pre.feature_names_in_))
    inst.preprocessor = pre
    inst.model = StubModel()

    results = inst.predict_batch([_transaction_dict(), _transaction_dict()])
    assert isinstance(results, list)
    assert len(results) == 2
