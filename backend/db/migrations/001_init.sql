-- ============================================================
-- AgentERP  –  Database Schema (PostgreSQL 16 + pgvector)
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";       -- pgvector

-- ── Enums ──────────────────────────────────────────────────
CREATE TYPE order_status AS ENUM (
    'draft', 'pending_review', 'approved', 'processing',
    'shipped', 'delivered', 'cancelled', 'returned'
);

CREATE TYPE agent_task_status AS ENUM (
    'queued', 'running', 'completed', 'failed', 'cancelled'
);

CREATE TYPE agent_type AS ENUM (
    'document_processor', 'order_agent', 'inventory_agent',
    'migration_agent', 'qa_agent', 'orchestrator'
);

-- ── Customers ──────────────────────────────────────────────
CREATE TABLE customers (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name        VARCHAR(255) NOT NULL,
    email       VARCHAR(255) UNIQUE NOT NULL,
    phone       VARCHAR(50),
    company     VARCHAR(255),
    address     JSONB DEFAULT '{}',
    metadata    JSONB DEFAULT '{}',
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ── Products ───────────────────────────────────────────────
CREATE TABLE products (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sku             VARCHAR(100) UNIQUE NOT NULL,
    name            VARCHAR(255) NOT NULL,
    description     TEXT,
    category        VARCHAR(100),
    unit_price      NUMERIC(12, 2) NOT NULL CHECK (unit_price >= 0),
    cost_price      NUMERIC(12, 2) CHECK (cost_price >= 0),
    quantity_on_hand INTEGER DEFAULT 0 CHECK (quantity_on_hand >= 0),
    reorder_point    INTEGER DEFAULT 10,
    reorder_quantity INTEGER DEFAULT 50,
    supplier_id     UUID,
    embedding       vector(1536),          -- OpenAI ada-002 dimension
    metadata        JSONB DEFAULT '{}',
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_products_embedding ON products USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX idx_products_category ON products (category);
CREATE INDEX idx_products_sku ON products (sku);

-- ── Suppliers ──────────────────────────────────────────────
CREATE TABLE suppliers (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name        VARCHAR(255) NOT NULL,
    contact     VARCHAR(255),
    email       VARCHAR(255),
    phone       VARCHAR(50),
    lead_time_days INTEGER DEFAULT 7,
    rating      NUMERIC(3, 2) DEFAULT 0,
    metadata    JSONB DEFAULT '{}',
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE products ADD CONSTRAINT fk_product_supplier
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id);

-- ── Orders ─────────────────────────────────────────────────
CREATE TABLE orders (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_number    VARCHAR(50) UNIQUE NOT NULL,
    customer_id     UUID NOT NULL REFERENCES customers(id),
    status          order_status DEFAULT 'draft',
    total_amount    NUMERIC(14, 2) DEFAULT 0,
    tax_amount      NUMERIC(14, 2) DEFAULT 0,
    shipping_amount NUMERIC(14, 2) DEFAULT 0,
    notes           TEXT,
    source          VARCHAR(50) DEFAULT 'manual',    -- manual / agent / legacy_import
    processed_by_agent UUID,                          -- which agent processed it
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_orders_status ON orders (status);
CREATE INDEX idx_orders_customer ON orders (customer_id);
CREATE INDEX idx_orders_created ON orders (created_at DESC);

-- ── Order Items ────────────────────────────────────────────
CREATE TABLE order_items (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id    UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id  UUID NOT NULL REFERENCES products(id),
    quantity    INTEGER NOT NULL CHECK (quantity > 0),
    unit_price  NUMERIC(12, 2) NOT NULL,
    total_price NUMERIC(14, 2) GENERATED ALWAYS AS (quantity * unit_price) STORED,
    metadata    JSONB DEFAULT '{}'
);

-- ── Inventory Transactions ─────────────────────────────────
CREATE TABLE inventory_transactions (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id      UUID NOT NULL REFERENCES products(id),
    transaction_type VARCHAR(50) NOT NULL,  -- purchase, sale, adjustment, return
    quantity_change  INTEGER NOT NULL,
    reference_id    UUID,                    -- order_id or purchase_order_id
    reason          TEXT,
    performed_by    VARCHAR(100) DEFAULT 'system',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_inv_tx_product ON inventory_transactions (product_id, created_at DESC);

-- ── Agent Tasks ────────────────────────────────────────────
CREATE TABLE agent_tasks (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_type      agent_type NOT NULL,
    status          agent_task_status DEFAULT 'queued',
    input_data      JSONB NOT NULL DEFAULT '{}',
    output_data     JSONB DEFAULT '{}',
    error_message   TEXT,
    parent_task_id  UUID REFERENCES agent_tasks(id),
    trace_id        VARCHAR(64),                      -- OpenTelemetry trace id
    tokens_used     INTEGER DEFAULT 0,
    cost_usd        NUMERIC(10, 6) DEFAULT 0,
    started_at      TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_agent_tasks_status ON agent_tasks (status);
CREATE INDEX idx_agent_tasks_type ON agent_tasks (agent_type);

-- ── Agent Execution Logs ───────────────────────────────────
CREATE TABLE agent_logs (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id     UUID NOT NULL REFERENCES agent_tasks(id) ON DELETE CASCADE,
    step_name   VARCHAR(100) NOT NULL,
    step_order  INTEGER NOT NULL,
    input_data  JSONB DEFAULT '{}',
    output_data JSONB DEFAULT '{}',
    llm_model   VARCHAR(50),
    tokens_in   INTEGER DEFAULT 0,
    tokens_out  INTEGER DEFAULT 0,
    duration_ms INTEGER,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ── Documents (legacy imports) ─────────────────────────────
CREATE TABLE documents (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    filename        VARCHAR(500) NOT NULL,
    content_type    VARCHAR(100),
    raw_text        TEXT,
    structured_data JSONB DEFAULT '{}',
    embedding       vector(1536),
    status          VARCHAR(50) DEFAULT 'pending',  -- pending, processing, processed, failed
    processed_by    UUID REFERENCES agent_tasks(id),
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_documents_embedding ON documents USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50);

-- ── Anomalies (detected by inventory agent) ────────────────
CREATE TABLE anomalies (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    anomaly_type    VARCHAR(100) NOT NULL,
    severity        VARCHAR(20) DEFAULT 'medium',  -- low, medium, high, critical
    entity_type     VARCHAR(50) NOT NULL,           -- product, order, customer
    entity_id       UUID NOT NULL,
    description     TEXT NOT NULL,
    recommendation  TEXT,
    is_resolved     BOOLEAN DEFAULT FALSE,
    detected_by     UUID REFERENCES agent_tasks(id),
    resolved_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_anomalies_unresolved ON anomalies (is_resolved, severity);

-- ── Updated_at trigger ─────────────────────────────────────
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_customers_updated BEFORE UPDATE ON customers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_products_updated BEFORE UPDATE ON products
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_orders_updated BEFORE UPDATE ON orders
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
