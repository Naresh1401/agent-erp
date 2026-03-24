-- Mart: Inventory health dashboard
WITH products AS (
    SELECT * FROM {{ ref('stg_products') }}
)

SELECT
    category,
    COUNT(*) AS product_count,
    COUNT(*) FILTER (WHERE stock_status = 'out_of_stock') AS out_of_stock,
    COUNT(*) FILTER (WHERE stock_status = 'low_stock') AS low_stock,
    COUNT(*) FILTER (WHERE stock_status = 'healthy') AS healthy_stock,
    COUNT(*) FILTER (WHERE stock_status = 'overstock') AS overstock,
    SUM(quantity_on_hand) AS total_units,
    SUM(quantity_on_hand * unit_price) AS total_inventory_value,
    SUM(quantity_on_hand * COALESCE(margin, 0)) AS potential_margin,
    AVG(unit_price) AS avg_unit_price,
    AVG(margin) AS avg_margin
FROM products
GROUP BY category
ORDER BY total_inventory_value DESC
