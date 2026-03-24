-- Staging: clean products + inventory data
WITH source AS (
    SELECT * FROM {{ source('erp', 'products') }}
)

SELECT
    id AS product_id,
    sku,
    name AS product_name,
    category,
    unit_price,
    cost_price,
    quantity_on_hand,
    reorder_point,
    reorder_quantity,
    is_active,
    (unit_price - COALESCE(cost_price, 0)) AS margin,
    CASE
        WHEN quantity_on_hand = 0 THEN 'out_of_stock'
        WHEN quantity_on_hand <= reorder_point THEN 'low_stock'
        WHEN quantity_on_hand > reorder_point * 5 THEN 'overstock'
        ELSE 'healthy'
    END AS stock_status,
    created_at,
    updated_at
FROM source
WHERE is_active = TRUE
