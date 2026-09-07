"""Tests for DataIngestion (src/components/data_ingestion.py).

Data is loaded from CSV files under the datasource/ directory.
"""

import pandas as pd
import pytest

from src.components.data_ingestion import DataIngestion
from utils.exception import FraudShieldException


def make_csv(tmp_path, records):
    path = tmp_path / "transactions.csv"
    pd.DataFrame(records).to_csv(path, index=False)
    return str(path)


def make_ingestion(path, limit=None):
    return DataIngestion(file_path=path, limit=limit)


def test_fetch_data_returns_dataframe(tmp_path):
    records = [
        {"transaction_amount": 100.0 + i, "transaction_is_fraud": i % 2}
        for i in range(5)
    ]
    df = make_ingestion(make_csv(tmp_path, records)).fetch_data()
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 5
    assert "transaction_amount" in df.columns
    assert "transaction_is_fraud" in df.columns


def test_fetch_data_applies_limit(tmp_path):
    records = [{"value": i} for i in range(10)]
    df = make_ingestion(make_csv(tmp_path, records), limit=3).fetch_data()
    assert len(df) == 3


def test_fetch_data_missing_file_raises(tmp_path):
    ing = make_ingestion(str(tmp_path / "nope.csv"))
    with pytest.raises(FraudShieldException):
        ing.fetch_data()


def test_fetch_data_empty_raises(tmp_path):
    ing = make_ingestion(make_csv(tmp_path, []))
    with pytest.raises(FraudShieldException):
        ing.fetch_data()


def test_default_path_points_to_train_datasource():
    assert DataIngestion().file_path.endswith("train_sampled.csv")