import pandas as pd

from ecommerce_analytics.features import FEATURE_COLUMNS
from ecommerce_analytics.modeling import (
    calculate_top_decile_metrics,
    evaluate_model,
    make_time_split,
    train_baseline_model,
    train_tree_model,
)


def make_modeling_frame() -> pd.DataFrame:
    rows = []
    for index in range(40):
        carts_cnt = 1 if index % 4 == 0 else 0
        purchase_flag = 1 if index % 5 == 0 else 0
        rows.append(
            {
                "session_id": f"session_{index}",
                "user_id": index % 8,
                "session_start": pd.Timestamp("2020-01-01") + pd.Timedelta(hours=index),
                "session_duration_minutes": 5 + index,
                "events_cnt": 2 + index % 6,
                "views_cnt": 1 + index % 4,
                "carts_cnt": carts_cnt,
                "distinct_products_cnt": 1 + index % 3,
                "distinct_categories_cnt": 1 + index % 2,
                "avg_price_viewed": 10.0 + index,
                "hour": index % 24,
                "day_of_week": index % 7,
                "is_weekend": 1 if index % 7 in {0, 6} else 0,
                "user_previous_sessions_cnt": index // 8,
                "user_previous_purchases_cnt": index // 20,
                "purchase_flag": purchase_flag,
            }
        )
    return pd.DataFrame(rows)


def test_make_time_split_uses_time_order() -> None:
    data = make_modeling_frame().sample(frac=1, random_state=42)

    train_data, test_data = make_time_split(data, train_size=0.75)

    assert train_data["session_start"].max() <= test_data["session_start"].min()
    assert len(train_data) == 30
    assert len(test_data) == 10


def test_calculate_top_decile_metrics() -> None:
    y_true = [1, 0, 0, 1, 0, 1, 0, 0, 0, 0]
    y_score = [0.99, 0.2, 0.1, 0.8, 0.3, 0.7, 0.4, 0.5, 0.6, 0.05]

    metrics = calculate_top_decile_metrics(y_true, y_score)

    assert metrics["precision_at_top_10_percent"] == 1.0
    assert metrics["purchase_capture_rate_at_top_10_percent"] == 1 / 3


def test_modeling_pipeline_on_small_dataframe() -> None:
    data = make_modeling_frame()
    train_data, test_data = make_time_split(data)

    baseline_model = train_baseline_model(train_data)
    tree_model = train_tree_model(train_data)

    baseline_metrics = evaluate_model(baseline_model, test_data)
    tree_metrics = evaluate_model(tree_model, test_data)

    assert set(FEATURE_COLUMNS).issubset(data.columns)
    assert "roc_auc" in baseline_metrics
    assert "pr_auc" in baseline_metrics
    assert "precision_at_top_10_percent" in tree_metrics
    assert "purchase_capture_rate_at_top_10_percent" in tree_metrics
