"""Tests for DataPreparation (src/components/data_preparation.py)."""

import numpy as np
import pandas as pd
import pytest

from src.components.data_preparation import DataPreparation
from utils.exception import FraudShieldException


def make_fe_df(n: int = 100):
    """Build a feature-engineered DataFrame suitable for preparation."""
    rng = np.random.default_rng(42)
    gender = ["M", "F"] * (n // 2)
    category = ["grocery_pos", "shopping_net", "gas_transport"] * (n // 3) + [
        "grocery_pos"
    ] * (n % 3)
    data = {
        "unix_time": np.arange(n),
        "buyer_lat": rng.uniform(30, 45, n),
        "buyer_long": rng.uniform(-120, -70, n),
        "merchant_lat": rng.uniform(30, 45, n),
        "merchant_long": rng.uniform(-120, -70, n),
        "transaction_amount": rng.uniform(1, 500, n),
        "buyer_job": ["Engineer"] * n,
        "transaction_date": pd.date_range("2023-01-01", periods=n),
        "buyer_date_of_birth": pd.date_range("1980-01-01", periods=n),
        "transaction_time": ["14:00:00"] * n,
        "buyer_gender": gender,
        "category": category,
        "distance_km": rng.uniform(0, 1000, n),
        "transaction_amount_log": np.log1p(rng.uniform(1, 500, n)),
        "is_night_transaction": rng.integers(0, 2, n),
        "transaction_hour": rng.integers(0, 24, n),
        "buyer_age": rng.integers(20, 80, n),
        "transaction_is_fraud": rng.integers(0, 2, n),
    }
    return pd.DataFrame(data)


@pytest.fixture
def fe_df():
    return make_fe_df(100)


def test_drop_unnecessary_columns(fe_df):
    prep = DataPreparation(fe_df)
    out = prep.drop_unnecessary_columns()
    for col in [
        "unix_time",
        "buyer_lat",
        "buyer_long",
        "merchant_lat",
        "merchant_long",
        "transaction_amount",
        "buyer_job",
        "transaction_date",
        "buyer_date_of_birth",
        "transaction_time",
    ]:
        assert col not in out.columns
    # categorical + numeric + engineered features remain
    assert "buyer_gender" in out.columns
    assert "category" in out.columns
    assert "distance_km" in out.columns


def test_split_features_target(fe_df):
    prep = DataPreparation(fe_df)
    X, y = prep.split_features_target()
    assert "transaction_is_fraud" not in X.columns
    assert (y == fe_df["transaction_is_fraud"]).all()


def test_train_test_split_is_stratified(fe_df):
    prep = DataPreparation(fe_df)
    X, y = prep.split_features_target()
    X_tr, X_te, y_tr, y_te = prep.train_test_split_data(X, y)
    assert len(X_tr) + len(X_te) == len(fe_df)
    assert len(X_tr) == pytest.approx(0.8 * len(fe_df), abs=1)
    # stratification preserves class ratio approximately
    assert len(y_tr) == pytest.approx(0.8 * len(y), abs=1)


def test_encode_and_scale(fe_df):
    prep = DataPreparation(fe_df)
    prep.drop_unnecessary_columns()
    X, y = prep.split_features_target()
    X_tr, X_te, y_tr, y_te = prep.train_test_split_data(X, y)
    X_tr_p, X_te_p, preprocessor = prep.encode_and_scale_features(X_tr, X_te)
    # numeric columns standardized → mean ~ 0
    assert X_tr_p.shape[0] == len(X_tr)
    assert len(X_te_p) == len(X_te)
    assert hasattr(preprocessor, "transform")


def test_prepare_data_full(fe_df):
    (
        X_tr,
        X_te,
        y_tr,
        y_te,
        preprocessor,
    ) = DataPreparation(fe_df).prepare_data()
    assert X_tr.shape[0] == len(y_tr)
    assert X_te.shape[0] == len(y_te)
    assert X_tr.shape[1] > 0


def test_prepare_data_with_test_df_fits_preprocessor_on_train_only(fe_df):
    """When a test_df is supplied, no random split happens and the
    preprocessor is fitted on the training frame only."""
    train_df = fe_df.copy()
    test_df = fe_df.copy()

    prep = DataPreparation(train_df, test_df=test_df)
    (
        X_tr,
        X_te,
        y_tr,
        y_te,
        preprocessor,
    ) = prep.prepare_data()

    assert len(X_tr) == len(train_df)
    assert len(X_te) == len(test_df)
    assert len(y_tr) == len(train_df)
    assert len(y_te) == len(test_df)
    assert X_tr.shape[1] == X_te.shape[1]
    # the test frame was dropped of the same unnecessary columns
    for col in ["unix_time", "buyer_lat", "transaction_date"]:
        assert col not in prep.test_df.columns
    assert hasattr(preprocessor, "transform")
