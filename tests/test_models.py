"""Tests for ModelTrainer / ModelEvaluation.

These use tiny synthetic datasets so training stays fast and offline.
MLflow's remote (DagsHub) connection is monkeypatched out so tests run
against the local file-based tracking store with no network/credentials.
"""

import numpy as np
import pandas as pd
import pytest

from src.components.model_trainer import ModelTrainer
from src.components.model_evaluation import ModelEvaluation


COLS = [
    "buyer_gender",
    "category",
    "distance_km",
    "transaction_amount_log",
    "is_night_transaction",
    "transaction_hour",
    "buyer_age",
]


def make_model_data(n: int = 300, positive_ratio: float = 0.3):
    rng = np.random.default_rng(7)
    df = pd.DataFrame(
        {
            "buyer_gender": rng.choice(["M", "F"], n),
            "category": rng.choice(
                ["grocery_pos", "shopping_net", "gas_transport"], n
            ),
            "distance_km": rng.uniform(0, 500, n),
            "transaction_amount_log": np.log1p(rng.uniform(1, 1200, n)),
            "is_night_transaction": rng.integers(0, 2, n),
            "transaction_hour": rng.integers(0, 24, n),
            "buyer_age": rng.integers(20, 80, n),
        }
    )
    # label with a simple, learnable rule involving night + amount
    score = (
        df["is_night_transaction"] * 2.0
        + df["transaction_amount_log"] / 10.0
        + (df["buyer_gender"] == "M").astype(int)
    )
    median = np.quantile(score, 1 - positive_ratio)
    y = (score >= median).astype(int)

    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler, OneHotEncoder
    from sklearn.compose import ColumnTransformer

    cat = ["buyer_gender", "category"]
    num = [c for c in COLS if c not in cat]
    preprocessor = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore"), cat),
            ("num", StandardScaler(), num),
        ]
    )
    X, Y = df.drop(columns=["transaction_is_fraud"]) if "transaction_is_fraud" in df else (df, y)
    X_tr, X_te, y_tr, y_te = train_test_split(df, y, test_size=0.2, random_state=42)
    X_tr = preprocessor.fit_transform(X_tr)
    X_te = preprocessor.transform(X_te)
    return X_tr, X_te, y_tr, y_te, preprocessor


@pytest.fixture
def model_data():
    return make_model_data(300)


def test_get_models_returns_four_with_class_weights(model_data):
    X_tr, X_te, y_tr, y_te, _ = model_data
    trainer = ModelTrainer(X_tr, X_te, y_tr, y_te)
    models = trainer.get_models()
    assert set(models.keys()) == {
        "Logistic Regression",
        "Decision Tree",
        "Random Forest",
        "XGBoost",
    }
    # XGBoost uses scale_pos_weight = negatives / positives
    xgb = models["XGBoost"]
    neg = (y_tr == 0).sum()
    pos = (y_tr == 1).sum()
    assert xgb.scale_pos_weight == pytest.approx(neg / pos)


def test_get_models_no_positive_samples(model_data):
    X_tr, X_te, y_tr, y_te, _ = model_data
    y_tr_all_neg = np.zeros_like(y_tr)
    trainer = ModelTrainer(X_tr, X_te, y_tr_all_neg, y_te)
    models = trainer.get_models()
    assert models["XGBoost"].scale_pos_weight == 1


def test_evaluate_model_returns_metrics(model_data):
    from sklearn.linear_model import LogisticRegression

    X_tr, X_te, y_tr, y_te, _ = model_data
    model = LogisticRegression(max_iter=500)
    model.fit(X_tr, y_tr)
    trainer = ModelTrainer(X_tr, X_te, y_tr, y_te)
    metrics = trainer.evaluate_model(model)
    assert set(metrics) == {"f1_score", "precision", "recall"}
    for v in metrics.values():
        assert 0.0 <= v <= 1.0


def test_train_models_selects_best_and_saves( tmp_path, monkeypatch, model_data):
    X_tr, X_te, y_tr, y_te, preprocessor = model_data
    trainer = ModelTrainer(X_tr, X_te, y_tr, y_te, preprocessor=preprocessor)

    # Skip the DagsHub/remote connection — use MLflow's default local file
    # store instead, so training tests run fully offline.
    monkeypatch.setattr(
        "src.components.model_trainer.init_mlflow",
        lambda: None,
    )
    # Isolate artifact writes to a temp dir
    monkeypatch.chdir(tmp_path)

    best_model, results = trainer.train_models()
    assert best_model is not None
    assert isinstance(results, list)
    assert len(results) == 4
    # each result has a Model name and metrics
    for r in results:
        assert "Model" in r
        assert "recall" in r
    # artifact files produced
    assert (tmp_path / "artifacts" / "best_model.pkl").exists()
    assert (tmp_path / "artifacts" / "preprocessor.pkl").exists()


def test_model_evaluation_returns_all_metrics(model_data):
    from sklearn.linear_model import LogisticRegression

    X_tr, X_te, y_tr, y_te, _ = model_data
    model = LogisticRegression(max_iter=500)
    model.fit(X_tr, y_tr)

    ev = ModelEvaluation(model, X_te, y_te)
    out = ev.evaluate()
    assert "classification_report" in out
    assert "confusion_matrix" in out
    assert "roc_auc_score" in out
    assert "pr_auc_score" in out
    assert 0.0 <= out["roc_auc_score"] <= 1.0
    assert 0.0 <= out["pr_auc_score"] <= 1.0
