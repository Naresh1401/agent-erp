-- Mart: Agent performance metrics
WITH tasks AS (
    SELECT * FROM {{ ref('stg_agent_tasks') }}
)

SELECT
    agent_type,
    COUNT(*) AS total_tasks,
    COUNT(*) FILTER (WHERE is_success) AS successful_tasks,
    COUNT(*) FILTER (WHERE NOT is_success) AS failed_tasks,
    ROUND(100.0 * COUNT(*) FILTER (WHERE is_success) / NULLIF(COUNT(*), 0), 1) AS success_rate_pct,
    AVG(duration_ms) AS avg_duration_ms,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY duration_ms) AS p50_duration_ms,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY duration_ms) AS p95_duration_ms,
    SUM(tokens_used) AS total_tokens,
    SUM(cost_usd) AS total_cost_usd,
    AVG(tokens_used) AS avg_tokens_per_task,
    AVG(cost_usd) AS avg_cost_per_task
FROM tasks
GROUP BY agent_type
ORDER BY total_tasks DESC
