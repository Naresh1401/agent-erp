-- Staging: clean orders data
WITH source AS (
    SELECT * FROM {{ source('erp', 'orders') }}
)

SELECT
    id AS order_id,
    order_number,
    customer_id,
    status,
    total_amount,
    tax_amount,
    shipping_amount,
    source AS order_source,
    processed_by_agent,
    created_at,
    updated_at,
    DATE(created_at) AS order_date,
    EXTRACT(YEAR FROM created_at) AS order_year,
    EXTRACT(MONTH FROM created_at) AS order_month
FROM source
