-- Staging: Agent task performance metrics
WITH source AS (
    SELECT * FROM {{ source('erp', 'agent_tasks') }}
)

SELECT
    id AS task_id,
    agent_type,
    status,
    tokens_used,
    cost_usd,
    started_at,
    completed_at,
    created_at,
    EXTRACT(EPOCH FROM (completed_at - started_at)) * 1000 AS duration_ms,
    CASE
        WHEN status = 'completed' THEN TRUE
        ELSE FALSE
    END AS is_success
FROM source
