from pathlib import Path

import duckdb
import pandas as pd

from ecommerce_analytics.build_marts import MARTS_DATABASE


FEATURE_COLUMNS = [
    "session_duration_minutes",
    "events_cnt",
    "views_cnt",
    "carts_cnt",
    "distinct_products_cnt",
    "distinct_categories_cnt",
    "avg_price_viewed",
    "hour",
    "day_of_week",
    "is_weekend",
    "user_previous_sessions_cnt",
    "user_previous_purchases_cnt",
]
TARGET_COLUMN = "purchase_flag"


def build_session_features(
    database_path: Path = MARTS_DATABASE,
    limit: int | None = None,
) -> pd.DataFrame:
    if not database_path.exists():
        raise FileNotFoundError(
            "Не найдена база data/marts/ecommerce.duckdb. "
            "Сначала запустите python scripts/build_marts.py."
        )

    limit_sql = f"LIMIT {limit}" if limit is not None else ""
    query = f"""
    WITH ordered_events AS (
        SELECT
            event_time,
            event_type,
            product_id,
            category_id,
            price,
            user_id,
            NULLIF(TRIM(CAST(user_session AS VARCHAR)), '') AS source_session_id,
            LAG(event_time) OVER (
                PARTITION BY user_id
                ORDER BY event_time, event_type, product_id
            ) AS previous_event_time
        FROM fct_events
    ),
    marked_events AS (
        SELECT
            *,
            CASE
                WHEN source_session_id IS NULL
                    AND (
                        previous_event_time IS NULL
                        OR DATE_DIFF('minute', previous_event_time, event_time) > 30
                    )
                    THEN 1
                ELSE 0
            END AS derived_session_start
        FROM ordered_events
    ),
    sessionized_events AS (
        SELECT
            *,
            CASE
                WHEN source_session_id IS NOT NULL THEN source_session_id
                ELSE CONCAT(
                    'derived_',
                    CAST(user_id AS VARCHAR),
                    '_',
                    CAST(
                        SUM(derived_session_start) OVER (
                            PARTITION BY user_id
                            ORDER BY event_time, event_type, product_id
                            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                        ) AS VARCHAR
                    )
                )
            END AS session_id
        FROM marked_events
    ),
    session_event_features AS (
        SELECT
            session_id,
            user_id,
            AVG(CASE WHEN event_type = 'view' THEN price ELSE NULL END) AS avg_price_viewed
        FROM sessionized_events
        GROUP BY session_id, user_id
    ),
    session_features AS (
        SELECT
            sessions.session_id,
            sessions.user_id,
            sessions.session_start,
            sessions.session_duration_minutes,
            sessions.events_cnt,
            sessions.views_cnt,
            sessions.carts_cnt,
            sessions.distinct_products_cnt,
            sessions.distinct_categories_cnt,
            COALESCE(session_event_features.avg_price_viewed, 0) AS avg_price_viewed,
            EXTRACT('hour' FROM sessions.session_start) AS hour,
            EXTRACT('dow' FROM sessions.session_start) AS day_of_week,
            CASE
                WHEN EXTRACT('dow' FROM sessions.session_start) IN (0, 6) THEN 1
                ELSE 0
            END AS is_weekend,
            COALESCE(
                COUNT(*) OVER (
                    PARTITION BY sessions.user_id
                    ORDER BY sessions.session_start, sessions.session_id
                    ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
                ),
                0
            ) AS user_previous_sessions_cnt,
            COALESCE(
                SUM(sessions.purchase_flag) OVER (
                    PARTITION BY sessions.user_id
                    ORDER BY sessions.session_start, sessions.session_id
                    ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
                ),
                0
            ) AS user_previous_purchases_cnt,
            sessions.purchase_flag
        FROM fct_sessions AS sessions
        LEFT JOIN session_event_features
            ON sessions.session_id = session_event_features.session_id
            AND sessions.user_id = session_event_features.user_id
    )
    SELECT *
    FROM session_features
    ORDER BY session_start, session_id
    {limit_sql}
    """

    with duckdb.connect(str(database_path), read_only=True) as connection:
        return connection.execute(query).fetchdf()
