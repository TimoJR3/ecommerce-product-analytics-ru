CREATE OR REPLACE TABLE mart_product_conversion AS
WITH product_events AS (
    SELECT
        product_id,
        category_code,
        brand,
        SUM(CASE WHEN event_type = 'view' THEN 1 ELSE 0 END) AS views_cnt,
        SUM(CASE WHEN event_type = 'cart' THEN 1 ELSE 0 END) AS carts_cnt,
        SUM(CASE WHEN event_type = 'purchase' THEN 1 ELSE 0 END) AS purchases_cnt,
        SUM(CASE WHEN event_type = 'purchase' THEN price ELSE 0 END) AS revenue
    FROM fct_events
    GROUP BY
        product_id,
        category_code,
        brand
)
SELECT
    product_id,
    category_code,
    brand,
    views_cnt,
    carts_cnt,
    purchases_cnt,
    revenue,
    purchases_cnt::DOUBLE / NULLIF(views_cnt, 0) AS conversion_rate
FROM product_events;
