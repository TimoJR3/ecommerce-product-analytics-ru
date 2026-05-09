from __future__ import annotations

import pandas as pd


def safe_divide(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return float(numerator) / float(denominator)


def calculate_funnel_metrics(
    views_cnt: int,
    carts_cnt: int,
    purchases_cnt: int,
) -> dict[str, float]:
    return {
        "view_to_cart_rate": safe_divide(carts_cnt, views_cnt),
        "cart_to_purchase_rate": safe_divide(purchases_cnt, carts_cnt),
        "purchase_conversion_rate": safe_divide(purchases_cnt, views_cnt),
    }


def calculate_repeat_purchase_rate(
    purchases_by_user: pd.DataFrame,
    user_column: str = "user_id",
    purchases_column: str = "purchases_cnt",
) -> float:
    if purchases_by_user.empty:
        return 0.0

    buyers = purchases_by_user[purchases_by_user[purchases_column] > 0]
    repeat_buyers = buyers[buyers[purchases_column] > 1]
    return safe_divide(len(repeat_buyers), len(buyers))


def calculate_abandoned_cart_share(
    sessions: pd.DataFrame,
    carts_column: str = "carts_cnt",
    purchases_column: str = "purchases_cnt",
) -> float:
    if sessions.empty:
        return 0.0

    sessions_with_cart = sessions[sessions[carts_column] > 0]
    abandoned_sessions = sessions_with_cart[sessions_with_cart[purchases_column] == 0]
    return safe_divide(len(abandoned_sessions), len(sessions_with_cart))
