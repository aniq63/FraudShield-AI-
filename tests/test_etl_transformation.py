"""Tests for the transformation component (DataTransformer)."""

import pandas as pd
import pytest

from src.components.data_transformation import DataTransformer
from utils.exception import FraudShieldException


RAW_COLUMNS = [
    "trans_num",
    "first",
    "last",
    "street",
    "Unnamed: 0",
    "cc_num",
    "amt",
    "lat",
    "long",
    "city",
    "state",
    "zip",
    "job",
    "dob",
    "city_pop",
    "merch_lat",
    "merch_long",
    "gender",
    "is_fraud",
    "trans_date_trans_time",
    "merchant",
    "category",
]


def make_raw_df():
    return pd.DataFrame(
        [
            {
                "trans_num": "t0",
                "first": "John",
                "last": "Doe",
                "street": "1 Main St",
                "Unnamed: 0": 0,
                "cc_num": "4000000000000000",
                "amt": 100.0,
                "lat": 40.7128,
                "long": -74.0060,
                "city": "Brooklyn",
                "state": "NY",
                "zip": 11211,
                "job": "Engineer",
                "dob": "1985-01-15",
                "city_pop": 2500000,
                "merch_lat": 40.7,
                "merch_long": -74.0,
                "gender": "M",
                "is_fraud": 0,
                "trans_date_trans_time": "2023-01-15 14:05:00",
                "merchant": "merchant_0",
                "category": "grocery_pos",
            }
        ]
    )


def test_drop_columns_removes_irrelevant():
    df = make_raw_df()
    tr = DataTransformer(df)
    tr.drop_columns()
    for col in ["trans_num", "first", "last", "street", "Unnamed: 0"]:
        assert col not in tr.df.columns


def test_handle_missing_values_drops_nan():
    df = make_raw_df()
    df.loc[0, "zip"] = None
    tr = DataTransformer(df)
    tr.handle_missing_values()
    assert tr.df.empty


def test_remove_duplicates():
    df = pd.concat([make_raw_df(), make_raw_df()], ignore_index=True)
    tr = DataTransformer(df)
    tr.remove_duplicates()
    assert len(tr.df) == 1


def test_process_datetime_splits_date_and_time():
    df = make_raw_df()
    tr = DataTransformer(df)
    tr.process_datetime()
    assert "trans_date_trans_time" not in tr.df.columns
    assert tr.df["transaction_date"].iloc[0] == pd.Timestamp("2023-01-15").date()
    assert str(tr.df["transaction_time"].iloc[0]) == "14:05:00"


def test_rename_columns():
    df = make_raw_df()
    tr = DataTransformer(df)
    tr.rename_columns()
    expected = {
        "cc_num": "credit_card_number",
        "amt": "transaction_amount",
        "lat": "buyer_lat",
        "long": "buyer_long",
        "gender": "buyer_gender",
        "is_fraud": "transaction_is_fraud",
    }
    for old, new in expected.items():
        assert old not in tr.df.columns
        assert new in tr.df.columns


def test_feature_engineering_computes_hour_and_age():
    df = make_raw_df()
    tr = DataTransformer(df)
    tr.process_datetime()
    tr.rename_columns()
    tr.convert_types()
    tr.feature_engineering()
    assert tr.df["transaction_hour"].iloc[0] == 14
    assert tr.df["buyer_age"].iloc[0] == 38


def test_full_transform_pipeline():
    df = make_raw_df()
    out = DataTransformer(df).transform()
    assert isinstance(out, pd.DataFrame)
    assert "transaction_amount" in out.columns
    assert "transaction_is_fraud" in out.columns
    assert "transaction_date" in out.columns
    # dropped columns are gone
    for col in ["trans_num", "first", "last", "street", "Unnamed: 0"]:
        assert col not in out.columns


def test_transform_raises_on_bad_types():
    df = make_raw_df()
    # corrupt is_fraud so type conversion fails
    df["is_fraud"] = "not-an-int"
    with pytest.raises(FraudShieldException):
        DataTransformer(df).transform()
