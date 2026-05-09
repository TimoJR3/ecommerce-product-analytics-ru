from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from ecommerce_analytics.config import MARTS_DATA_DIR, REPORTS_DIR
from ecommerce_analytics.features import FEATURE_COLUMNS, TARGET_COLUMN
from ecommerce_analytics.metrics import safe_divide


METRICS_PATH = REPORTS_DIR / "propensity_metrics.json"
SCORES_PATH = MARTS_DATA_DIR / "propensity_scores.parquet"


def make_time_split(
    data: pd.DataFrame,
    time_column: str = "session_start",
    train_size: float = 0.8,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if data.empty:
        raise ValueError("Нельзя построить time split на пустом датафрейме.")

    if not 0 < train_size < 1:
        raise ValueError("train_size должен быть между 0 и 1.")

    sorted_data = data.sort_values(time_column).reset_index(drop=True)
    split_index = int(len(sorted_data) * train_size)
    split_index = min(max(split_index, 1), len(sorted_data) - 1)
    return sorted_data.iloc[:split_index].copy(), sorted_data.iloc[split_index:].copy()


def train_baseline_model(
    train_data: pd.DataFrame,
    feature_columns: list[str] = FEATURE_COLUMNS,
    target_column: str = TARGET_COLUMN,
) -> Pipeline:
    model = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            (
                "classifier",
                LogisticRegression(max_iter=1000, class_weight="balanced"),
            ),
        ]
    )
    model.fit(train_data[feature_columns], train_data[target_column])
    return model


def train_tree_model(
    train_data: pd.DataFrame,
    feature_columns: list[str] = FEATURE_COLUMNS,
    target_column: str = TARGET_COLUMN,
) -> Pipeline:
    model = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            (
                "classifier",
                HistGradientBoostingClassifier(
                    max_iter=100,
                    learning_rate=0.08,
                    l2_regularization=0.1,
                    random_state=42,
                ),
            ),
        ]
    )
    model.fit(train_data[feature_columns], train_data[target_column])
    return model


def _predict_score(model: Pipeline, data: pd.DataFrame) -> np.ndarray:
    if hasattr(model, "predict_proba"):
        return model.predict_proba(data)[:, 1]
    return model.decision_function(data)


def evaluate_model(
    model: Pipeline,
    test_data: pd.DataFrame,
    feature_columns: list[str] = FEATURE_COLUMNS,
    target_column: str = TARGET_COLUMN,
) -> dict[str, float]:
    y_true = test_data[target_column].astype(int).to_numpy()
    y_score = _predict_score(model, test_data[feature_columns])

    if len(np.unique(y_true)) < 2:
        roc_auc = 0.0
        pr_auc = 0.0
    else:
        roc_auc = float(roc_auc_score(y_true, y_score))
        pr_auc = float(average_precision_score(y_true, y_score))

    top_decile = calculate_top_decile_metrics(y_true, y_score)
    return {
        "roc_auc": roc_auc,
        "pr_auc": pr_auc,
        **top_decile,
    }


def calculate_top_decile_metrics(
    y_true: pd.Series | np.ndarray,
    y_score: pd.Series | np.ndarray,
    top_share: float = 0.1,
) -> dict[str, float]:
    if not 0 < top_share <= 1:
        raise ValueError("top_share должен быть в диапазоне от 0 до 1.")

    truth = np.asarray(y_true).astype(int)
    score = np.asarray(y_score).astype(float)

    if len(truth) == 0:
        return {
            "precision_at_top_10_percent": 0.0,
            "purchase_capture_rate_at_top_10_percent": 0.0,
        }

    top_n = max(1, int(np.ceil(len(truth) * top_share)))
    top_indices = np.argsort(score)[::-1][:top_n]
    top_purchases = int(truth[top_indices].sum())
    total_purchases = int(truth.sum())

    return {
        "precision_at_top_10_percent": safe_divide(top_purchases, top_n),
        "purchase_capture_rate_at_top_10_percent": safe_divide(
            top_purchases,
            total_purchases,
        ),
    }


def save_metrics(metrics: dict[str, dict[str, float]], output_path: Path = METRICS_PATH) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return output_path


def save_scores(
    data: pd.DataFrame,
    baseline_model: Pipeline,
    tree_model: Pipeline,
    output_path: Path = SCORES_PATH,
    feature_columns: list[str] = FEATURE_COLUMNS,
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    scores = data[["session_id", "user_id", "session_start", TARGET_COLUMN]].copy()
    scores["baseline_score"] = _predict_score(baseline_model, data[feature_columns])
    scores["model_score"] = _predict_score(tree_model, data[feature_columns])
    scores.to_parquet(output_path, index=False)
    return output_path
