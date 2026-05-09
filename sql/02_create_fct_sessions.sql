CREATE OR REPLACE TABLE fct_sessions AS
WITH ordered_events AS (
    SELECT
        event_time,
        event_type,
        product_id,
        category_id,
        category_code,
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
)
SELECT
    session_id,
    user_id,
    MIN(event_time) AS session_start,
    MAX(event_time) AS session_end,
    COUNT(*) AS events_cnt,
    SUM(CASE WHEN event_type = 'view' THEN 1 ELSE 0 END) AS views_cnt,
    SUM(CASE WHEN event_type = 'cart' THEN 1 ELSE 0 END) AS carts_cnt,
    SUM(CASE WHEN event_type = 'purchase' THEN 1 ELSE 0 END) AS purchases_cnt,
    MAX(CASE WHEN event_type = 'purchase' THEN 1 ELSE 0 END) AS purchase_flag,
    SUM(CASE WHEN event_type = 'purchase' THEN price ELSE 0 END) AS revenue,
    DATE_DIFF('minute', MIN(event_time), MAX(event_time)) AS session_duration_minutes,
    COUNT(DISTINCT product_id) AS distinct_products_cnt,
    COUNT(DISTINCT category_id) AS distinct_categories_cnt
FROM sessionized_events
GROUP BY
    session_id,
    user_id;
