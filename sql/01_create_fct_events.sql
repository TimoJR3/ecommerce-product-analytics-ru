CREATE OR REPLACE TABLE fct_events AS
SELECT
    CAST(event_time AS TIMESTAMP) AS event_time,
    CAST(event_time AS DATE) AS event_date,
    event_type,
    product_id,
    category_id,
    category_code,
    brand,
    CAST(price AS DOUBLE) AS price,
    user_id,
    user_session
FROM read_parquet('{{EVENTS_PARQUET}}');
