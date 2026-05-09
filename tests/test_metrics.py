import pandas as pd

from ecommerce_analytics.metrics import (
    calculate_abandoned_cart_share,
    calculate_funnel_metrics,
    calculate_repeat_purchase_rate,
    safe_divide,
)


def test_safe_divide_returns_zero_for_zero_denominator() -> None:
    assert safe_divide(10, 0) == 0.0


def test_safe_divide_returns_ratio() -> None:
    assert safe_divide(2, 4) == 0.5


def test_calculate_funnel_metrics() -> None:
    metrics = calculate_funnel_metrics(views_cnt=100, carts_cnt=20, purchases_cnt=5)

    assert metrics["view_to_cart_rate"] == 0.2
    assert metrics["cart_to_purchase_rate"] == 0.25
    assert metrics["purchase_conversion_rate"] == 0.05


def test_calculate_repeat_purchase_rate() -> None:
    purchases_by_user = pd.DataFrame(
        {
            "user_id": [1, 2, 3, 4],
            "purchases_cnt": [1, 2, 0, 3],
        }
    )

    assert calculate_repeat_purchase_rate(purchases_by_user) == 2 / 3


def test_calculate_abandoned_cart_share() -> None:
    sessions = pd.DataFrame(
        {
            "session_id": ["a", "b", "c", "d"],
            "carts_cnt": [1, 2, 0, 1],
            "purchases_cnt": [0, 1, 0, 0],
        }
    )

    assert calculate_abandoned_cart_share(sessions) == 2 / 3
