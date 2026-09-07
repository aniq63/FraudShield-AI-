"""Integration tests: chain the offline ML data components together.

Transformation → Feature Engineering → Preparation must produce a trainable
feature matrix from raw Kaggle-shaped data, without any external services.
Also verifies the train-file / test-file preparation flow.
"""

import pandas as pd
import pytest

from src.components.data_transformation import DataTransformer
from src.components.data_feature_engineering import FeatureEngineer
from src.components.data_preparation import DataPreparation


def make_raw(n=100):
    """Small dataframe shaped like the raw Kaggle CSV."""
    import numpy as np

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
                "amt": 50.0 + i,
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
                "gender": "M" if i % 2 else "F",
                "is_fraud": 1 if i % 10 == 0 else 0,
                "trans_date_trans_time": f"2023-01-0{(i % 9) + 1} 2{i % 3}:0{i % 10}:00",
                "merchant": f"merchant_{i % 3}",
                "category": ["grocery_pos", "shopping_net", "gas_transport"][i % 3],
            }
        )
    return pd.DataFrame(rows)


def test_full_offline_ml_data_chain():
    raw = make_raw(100)

    # 1. Transformation
    clean = DataTransformer(raw).transform()
    assert "transaction_hour" in clean.columns
    assert "buyer_age" in clean.columns
    assert "transaction_is_fraud" in clean.columns

    # 2. Feature engineering
    engineered = FeatureEngineer(clean).engineer_features()
    for col in ["distance_km", "transaction_amount_log", "is_night_transaction"]:
        assert col in engineered.columns
    # numeric distance is a real (non-NaN) value
    assert engineered["distance_km"].notna().all()
    assert engineered["transaction_amount_log"].notna().all()

    # 3. Preparation
    (
        X_train,
        X_test,
        y_train,
        y_test,
        preprocessor,
    ) = DataPreparation(engineered).prepare_data()

    assert len(X_train) > 0 and len(X_test) > 0
    assert X_train.shape[1] == X_test.shape[1]
    assert len(y_train) == X_train.shape[0]
    assert len(y_test) == X_test.shape[0]
    # both classes present so the model can learn a boundary
    assert set(y_train.unique()) == {0, 1}


def test_pipeline_produces_nonconstant_fraud_rate():
    raw = make_raw(200)
    clean = DataTransformer(raw).transform()
    engineered = FeatureEngineer(clean).engineer_features()
    fraud_rate = engineered["transaction_is_fraud"].mean()
    assert 0 < fraud_rate < 1


def test_prepare_with_separate_train_and_test_files():
    """Preprocessor fits on the train file and transforms the test file."""
    train_raw = make_raw(150)
    test_raw = make_raw(50)

    train = FeatureEngineer(DataTransformer(train_raw).transform()).engineer_features()
    test = FeatureEngineer(DataTransformer(test_raw).transform()).engineer_features()

    (
        X_train,
        X_test,
        y_train,
        y_test,
        preprocessor,
    ) = DataPreparation(train, test_df=test).prepare_data()

    assert len(X_train) == len(train)
    assert len(X_test) == len(test)
    assert len(y_train) == len(train)
    assert len(y_test) == len(test)
    assert X_train.shape[1] == X_test.shape[1]
    assert set(y_train.unique()) == {0, 1}
    assert hasattr(preprocessor, "transform")
