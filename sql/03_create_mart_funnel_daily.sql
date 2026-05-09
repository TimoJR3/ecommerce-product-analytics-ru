CREATE OR REPLACE TABLE mart_funnel_daily AS
WITH daily_events AS (
    SELECT
        event_date,
        category_code,
        brand,
        SUM(CASE WHEN event_type = 'view' THEN 1 ELSE 0 END) AS views_cnt,
        SUM(CASE WHEN event_type = 'cart' THEN 1 ELSE 0 END) AS carts_cnt,
        SUM(CASE WHEN event_type = 'purchase' THEN 1 ELSE 0 END) AS purchases_cnt,
        SUM(CASE WHEN event_type = 'purchase' THEN price ELSE 0 END) AS revenue
    FROM fct_events
    GROUP BY
        event_date,
        category_code,
        brand
)
SELECT
    event_date,
    category_code,
    brand,
    views_cnt,
    carts_cnt,
    purchases_cnt,
    carts_cnt::DOUBLE / NULLIF(views_cnt, 0) AS view_to_cart_rate,
    purchases_cnt::DOUBLE / NULLIF(carts_cnt, 0) AS cart_to_purchase_rate,
    purchases_cnt::DOUBLE / NULLIF(views_cnt, 0) AS purchase_conversion_rate,
    revenue
FROM daily_events;
