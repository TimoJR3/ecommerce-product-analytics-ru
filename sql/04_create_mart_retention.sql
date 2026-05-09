CREATE OR REPLACE TABLE mart_retention AS
WITH purchases AS (
    SELECT
        user_id,
        DATE_TRUNC('month', event_time)::DATE AS order_month
    FROM fct_events
    WHERE event_type = 'purchase'
),
first_purchases AS (
    SELECT
        user_id,
        MIN(order_month) AS cohort_month
    FROM purchases
    GROUP BY user_id
),
cohort_sizes AS (
    SELECT
        cohort_month,
        COUNT(DISTINCT user_id) AS cohort_size
    FROM first_purchases
    GROUP BY cohort_month
),
cohort_activity AS (
    SELECT DISTINCT
        first_purchases.cohort_month,
        purchases.order_month,
        purchases.user_id
    FROM purchases
    INNER JOIN first_purchases
        ON purchases.user_id = first_purchases.user_id
)
SELECT
    cohort_activity.cohort_month,
    cohort_activity.order_month,
    DATE_DIFF(
        'month',
        cohort_activity.cohort_month,
        cohort_activity.order_month
    ) AS months_since_first_purchase,
    COUNT(DISTINCT cohort_activity.user_id) AS active_users,
    cohort_sizes.cohort_size,
    COUNT(DISTINCT cohort_activity.user_id)::DOUBLE
        / NULLIF(cohort_sizes.cohort_size, 0) AS retention_rate
FROM cohort_activity
INNER JOIN cohort_sizes
    ON cohort_activity.cohort_month = cohort_sizes.cohort_month
GROUP BY
    cohort_activity.cohort_month,
    cohort_activity.order_month,
    cohort_sizes.cohort_size;
