-- Mart: Order analytics – daily summary with agent vs manual breakdown
WITH orders AS (
    SELECT * FROM {{ ref('stg_orders') }}
),

order_items AS (
    SELECT
        order_id,
        COUNT(*) AS item_count,
        SUM(quantity) AS total_units
    FROM {{ source('erp', 'order_items') }}
    GROUP BY order_id
)

SELECT
    o.order_date,
    o.order_year,
    o.order_month,
    COUNT(DISTINCT o.order_id) AS total_orders,
    COUNT(DISTINCT o.order_id) FILTER (WHERE o.order_source = 'agent') AS agent_orders,
    COUNT(DISTINCT o.order_id) FILTER (WHERE o.order_source = 'manual') AS manual_orders,
    SUM(o.total_amount) AS total_revenue,
    AVG(o.total_amount) AS avg_order_value,
    SUM(o.tax_amount) AS total_tax,
    SUM(oi.item_count) AS total_line_items,
    SUM(oi.total_units) AS total_units_sold,
    COUNT(DISTINCT o.order_id) FILTER (WHERE o.status = 'cancelled') AS cancelled_orders,
    COUNT(DISTINCT o.order_id) FILTER (WHERE o.status = 'returned') AS returned_orders
FROM orders o
LEFT JOIN order_items oi ON o.order_id = oi.order_id
GROUP BY o.order_date, o.order_year, o.order_month
ORDER BY o.order_date DESC
