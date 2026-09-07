"""Tests for FeatureEngineer (src/components/data_feature_engineering.py)."""

import numpy as np
import pandas as pd
import pytest

from src.components.data_feature_engineering import FeatureEngineer
from utils.exception import FraudShieldException


def haversine(lat1, lon1, lat2, lon2):
    """Reference haversine implementation for comparison."""
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = (
        np.sin(dlat / 2) ** 2
        + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    )
    return R * 2 * np.arcsin(np.sqrt(a))


@pytest.fixture
def fe_df():
    return pd.DataFrame(
        {
            "transaction_date": ["2023-01-15", "2023-06-01"],
            "buyer_date_of_birth": ["1985-01-15", "1990-05-20"],
            "buyer_lat": [40.7128, 34.0522],
            "buyer_long": [-74.0060, -118.2437],
            "merchant_lat": [40.7000, 34.0500],
            "merchant_long": [-74.0000, -118.2400],
            "transaction_amount": [100.0, 0.0],
            "transaction_hour": [23, 5],
            "merchant": ["m1", "m2"],
            "credit_card_number": ["111", "222"],
            "buyer_city": ["NYC", "LA"],
            "buyer_state": ["NY", "CA"],
            "buyer_zip": [11211, 90001],
            "buyer_city_pop": [1000, 2000],
        }
    )


def test_convert_datetime_columns(fe_df):
    fe = FeatureEngineer(fe_df)
    fe.convert_datetime_columns()
    assert pd.api.types.is_datetime64_any_dtype(fe.df["transaction_date"])
    assert pd.api.types.is_datetime64_any_dtype(fe.df["buyer_date_of_birth"])


def test_create_distance_feature(fe_df):
    fe = FeatureEngineer(fe_df)
    fe.create_distance_feature()
    row = fe_df.iloc[0]
    expected = haversine(
        row["buyer_lat"], row["buyer_long"], row["merchant_lat"], row["merchant_long"]
    )
    assert "distance_km" in fe.df.columns
    assert fe.df["distance_km"].iloc[0] == pytest.approx(expected, rel=1e-6)
    assert (fe.df["distance_km"] >= 0).all()


def test_transform_transaction_amount(fe_df):
    fe = FeatureEngineer(fe_df)
    fe.transform_transaction_amount()
    assert "transaction_amount_log" in fe.df.columns
    assert fe.df["transaction_amount_log"].iloc[0] == pytest.approx(
        np.log1p(100.0)
    )


def test_create_night_transaction_flag(fe_df):
    fe = FeatureEngineer(fe_df)
    fe.create_night_transaction_flag()
    # hour 23 → night (1), hour 5 → not night (0)
    assert fe.df["is_night_transaction"].iloc[0] == 1
    assert fe.df["is_night_transaction"].iloc[1] == 0


def test_drop_unused_columns(fe_df):
    fe = FeatureEngineer(fe_df)
    fe.drop_unused_columns()
    for col in [
        "merchant",
        "credit_card_number",
        "buyer_city",
        "buyer_state",
        "buyer_zip",
        "buyer_city_pop",
    ]:
        assert col not in fe.df.columns


def test_engineer_features_full(fe_df):
    out = FeatureEngineer(fe_df).engineer_features()
    for col in ["distance_km", "transaction_amount_log", "is_night_transaction"]:
        assert col in out.columns
    for col in ["merchant", "buyer_city", "buyer_state"]:
        assert col not in out.columns
    assert len(out) == 2
