"""
Shared pytest fixtures for the FraudShield AI test suite.

These fixtures build small synthetic pandas DataFrames that mirror the
shape of the real Kaggle fraud dataset (both the raw/raw-ETL form and the
feature-engineered form), so component tests can run offline.
"""

import pandas as pd
import pytest


class FakeConsumer:
    """Stand-in for FraudPipelineConsumer used when importing api.routes.

    api.routes starts a FraudPipelineConsumer singleton at import time; this
    fake records start()/stop() without loading models from S3.
    """

    def __init__(self, result_callback=None, **kwargs):
        self.result_callback = result_callback
        self.started = False

    def start(self):
        self.started = True

    def stop(self):
        self.started = False


def _raw_transaction_frame(n: int = 10) -> pd.DataFrame:
    """Build a minimal DataFrame shaped like the raw Kaggle CSV."""
    rows = []
    for i in range(n):
        rows.append(
            {
                "trans_num": f"t{i}",
                "first": "John",
                "last": "Doe",
                "street": f"{i} Main St",
                "Unnamed: 0": i,
                "cc_num": f"4000{i:08d}",
                "amt": 50.0 + i * 10.0,
                "lat": 40.7128 + i * 0.1,
                "long": -74.0060 + i * 0.1,
                "city": "Brooklyn",
                "state": "NY",
                "zip": 11211,
                "job": "Engineer",
                "dob": "1985-01-15",
                "city_pop": 2500000,
                "merch_lat": 40.7 + i * 0.05,
                "merch_long": -74.0 + i * 0.05,
                "gender": "M",
                "is_fraud": i % 5 == 0,
                "trans_date_trans_time": f"2023-01-0{(i % 9) + 1} 14:0{i % 10}:00",
                "merchant": f"merchant_{i % 3}",
                "category": "grocery_pos",
            }
        )
    return pd.DataFrame(rows)


@pytest.fixture
def raw_transaction_frame() -> pd.DataFrame:
    """Raw Kaggle-shaped transaction data (pre-ETL)."""
    return _raw_transaction_frame(10)


@pytest.fixture
def transformed_frame() -> pd.DataFrame:
    """DataFrame already run through DataTransformer (post-ETL, pre-FE)."""
    rows = []
    for i in range(10):
        rows.append(
            {
                "credit_card_number": f"4000{i:08d}",
                "transaction_amount": 50.0 + i * 10.0,
                "buyer_lat": 40.7128 + i * 0.1,
                "buyer_long": -74.0060 + i * 0.1,
                "buyer_city": "Brooklyn",
                "buyer_state": "NY",
                "buyer_zip": 11211,
                "buyer_job": "Engineer",
                "buyer_date_of_birth": pd.Timestamp("1985-01-15"),
                "buyer_city_pop": 2500000,
                "merchant_lat": 40.7 + i * 0.05,
                "merchant_long": -74.0 + i * 0.05,
                "merchant": f"merchant_{i % 3}",
                "buyer_gender": "M",
                "transaction_is_fraud": i % 5 == 0,
                "transaction_date": pd.Timestamp("2023-01-15"),
                "transaction_time": f"14:0{i % 10}:00",
                "transaction_hour": 14,
                "buyer_age": 38,
                "category": "grocery_pos",
            }
        )
    return pd.DataFrame(rows)


@pytest.fixture
def feature_engineered_frame() -> pd.DataFrame:
    """DataFrame shaped like FeatureEngineer output (pre-Preparation)."""
    df = transformed_frame().copy()
    df["distance_km"] = 0.5
    df["transaction_amount_log"] = df["transaction_amount"].apply(
        lambda x: (x + 1) ** 0.5
    )
    df["is_night_transaction"] = 0
    return df
