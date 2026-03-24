# 🤖 AgentERP — AI-Powered ERP Modernization Platform

> Autonomous agents that transform legacy ERP systems into modern, AI-driven platforms.
> Built by the **Modernization Strike Team**.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![TypeScript](https://img.shields.io/badge/TypeScript-5.4-blue)
![LangGraph](https://img.shields.io/badge/LangGraph-0.0.55-green)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-teal)
![Docker](https://img.shields.io/badge/Docker-Compose-blue)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16+pgvector-blue)

---

## 🎯 What This Project Does

AgentERP demonstrates a **production-grade architecture** where autonomous AI agents handle complex enterprise operations that traditionally require manual work:

| Agent | What It Does | Tech |
|-------|-------------|------|
| **Document Processor** | Ingests legacy PDFs/docs → classifies → extracts structured data → generates embeddings | LangGraph, GPT-4o, pgvector |
| **Order Agent** | Validates → checks inventory → calculates pricing → risk assessment → auto-approve/escalate | LangGraph, GPT-4o |
| **Inventory Intelligence** | Analyzes stock → detects anomalies → forecasts demand → generates reorder recommendations | LangGraph, GPT-4o |
| **Migration Agent** | Analyzes legacy schemas → maps fields → generates transformation rules → produces migration plans | LangGraph, GPT-4o |
| **Orchestrator** | Central dispatcher that routes tasks, tracks execution, logs every step | Python async |
| **Background Worker** | Processes queued agent tasks asynchronously via Redis | Redis, asyncio |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     React + TypeScript Frontend                  │
│  Dashboard │ Agent Monitor │ Orders │ Inventory │ Docs │ Migration│
└──────────────────────────┬──────────────────────────────────────┘
                           │ REST API
┌──────────────────────────▼──────────────────────────────────────┐
│                    FastAPI Backend (Python)                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │ Orders   │ │Inventory │ │  Agents  │ │Analytics │          │
│  │  API     │ │   API    │ │   API    │ │   API    │          │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘          │
│       │             │            │             │                 │
│  ┌────▼─────────────▼────────────▼─────────────▼─────────────┐ │
│  │              Agent Orchestrator                             │ │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐            │ │
│  │  │  Document   │ │   Order    │ │ Inventory  │            │ │
│  │  │ Processor   │ │   Agent    │ │   Agent    │  LangGraph │ │
│  │  │  (5 nodes)  │ │ (6 nodes)  │ │ (4 nodes)  │            │ │
│  │  └────────────┘ └────────────┘ └────────────┘            │ │
│  │  ┌────────────┐                                           │ │
│  │  │ Migration  │                                           │ │
│  │  │   Agent    │                                           │ │
│  │  │ (4 nodes)  │                                           │ │
│  │  └────────────┘                                           │ │
│  └───────────────────────────────────────────────────────────┘ │
└────────┬──────────┬──────────┬──────────┬──────────┬───────────┘
         │          │          │          │          │
    ┌────▼────┐ ┌──▼───┐ ┌───▼──┐ ┌────▼────┐ ┌──▼──────┐
    │Postgres │ │Qdrant│ │Redis │ │  OTel   │ │  W&B    │
    │+pgvector│ │Vector│ │Queue │ │Collector│ │Tracking │
    │         │ │  DB  │ │      │ │+Jaeger  │ │         │
    └─────────┘ └──────┘ └──────┘ └─────────┘ └─────────┘
```

---

## 🛠️ Full Tech Stack

| Category | Technologies |
|----------|-------------|
| **Backend** | Python 3.12, FastAPI, SQLAlchemy (async), Pydantic v2 |
| **AI/LLM** | LangChain, LangGraph, OpenAI GPT-4o, Anthropic Claude, tiktoken |
| **Database** | PostgreSQL 16 + pgvector (vector similarity search) |
| **Vector Store** | Qdrant (semantic document search) |
| **Queue** | Redis (async agent task processing) |
| **Data Transform** | dbt (staging models → analytics marts) |
| **Frontend** | TypeScript, React 18, TailwindCSS, Chart.js |
| **Observability** | OpenTelemetry, Jaeger (traces), Prometheus (metrics), Grafana (dashboards), Weights & Biases |
| **Infrastructure** | Docker, Docker Compose (10 services) |
| **Testing** | pytest, pytest-asyncio, Playwright (E2E) |

---

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- OpenAI API key (for agent LLM calls)

### 1. Clone & Configure

```bash
cd agent-erp
cp .env.example .env
# Edit .env → add your OPENAI_API_KEY (and optionally ANTHROPIC_API_KEY)
```

### 2. Deploy (one command)

```bash
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

This will:
- Build all Docker images
- Start 10 services (Postgres, Qdrant, Redis, Backend, Worker, Frontend, OTel, Jaeger, Prometheus, Grafana)
- Run database migrations
- Seed with realistic demo data (22 products, 8 customers, 50 orders, 4 suppliers)

### 3. Access

| Service | URL |
|---------|-----|
| **Frontend** | http://localhost:3000 |
| **API Docs** (Swagger) | http://localhost:8000/docs |
| **Jaeger** (Traces) | http://localhost:16686 |
| **Grafana** (Dashboards) | http://localhost:3001 |
| **Prometheus** (Metrics) | http://localhost:9090 |

---

## 📋 Demo Walkthrough

### 1. Dashboard (http://localhost:3000)
See real-time stats: orders, products, customers, agent tasks, active anomalies with interactive charts.

### 2. Agent Monitor (http://localhost:3000/agents)
**This is the star of the show.** Four autonomous agents you can dispatch with one click:

#### 🔹 Document Processor
Paste a legacy invoice or PO → AI classifies it, extracts structured fields, validates, and generates vector embeddings for semantic search.

#### 🔹 Order Agent
Submit an order → AI validates data, checks inventory, calculates pricing with tax/shipping, runs fraud detection, and auto-approves or escalates.

#### 🔹 Inventory Intelligence
Analyzes all products → detects stockouts, low stock, overstock → uses LLM for pattern detection → generates demand forecast and reorder recommendations.

#### 🔹 Data Migration Agent
Feed it a legacy schema (cryptic `tbl_cust.CUST_NO` style) → AI maps every field to the modern schema, generates SQL/Python transformations, validates against sample data, and produces a complete migration plan.

### 3. Semantic Document Search
Upload documents → search by meaning (not just keywords) using Qdrant vector similarity.

### 4. Observability
Every agent execution is traced end-to-end via OpenTelemetry → viewable in Jaeger with per-step timing and token usage.

---

## 🧪 Testing

```bash
# Unit tests (no LLM calls needed)
docker-compose exec backend pytest tests/test_agents.py -v

# API tests
docker-compose exec backend pytest tests/test_api.py -v

# E2E tests (requires running frontend)
docker-compose exec backend playwright install chromium
docker-compose exec backend pytest tests/playwright/ -v
```

---

## 📊 dbt Analytics

The dbt layer transforms raw operational data into analytics-ready models:

```
models/
├── staging/           # Cleaned source data
│   ├── stg_orders.sql
│   ├── stg_products.sql
│   └── stg_agent_tasks.sql
└── marts/             # Business-ready aggregations
    ├── order_analytics.sql     # Daily revenue, agent vs manual breakdown
    ├── inventory_health.sql    # Stock status by category, inventory value
    └── agent_performance.sql   # Success rates, p50/p95 latency, cost per task
```

Run transformations:
```bash
cd backend/dbt
dbt run --profiles-dir .
```

---

## 🔧 API Reference

All endpoints are documented at http://localhost:8000/docs. Key routes:

```
POST /api/v1/agents/dispatch          # Dispatch an autonomous agent
GET  /api/v1/agents/tasks             # List all agent tasks
GET  /api/v1/agents/tasks/{id}/logs   # View step-by-step execution logs

GET  /api/v1/orders/                  # List orders
POST /api/v1/orders/                  # Create order
GET  /api/v1/orders/stats/summary     # Order statistics

GET  /api/v1/inventory/products       # List products
GET  /api/v1/inventory/alerts         # Low stock alerts
POST /api/v1/inventory/products/{id}/adjust  # Adjust stock

POST /api/v1/documents/upload         # Upload & process document with AI
POST /api/v1/documents/search         # Semantic search

GET  /api/v1/analytics/dashboard      # Full dashboard data
```

---

## 🏛️ Project Structure

```
agent-erp/
├── docker-compose.yml              # 10-service orchestration
├── Dockerfile.backend              # Python API image
├── Dockerfile.frontend             # React production image
├── .env.example                    # Configuration template
│
├── backend/
│   ├── main.py                     # FastAPI app entry point
│   ├── config.py                   # Pydantic settings
│   ├── db/
│   │   ├── database.py             # Async SQLAlchemy engine
│   │   ├── models.py               # ORM models (10 tables)
│   │   └── migrations/001_init.sql # Full schema + pgvector
│   ├── api/
│   │   ├── schemas.py              # Pydantic request/response models
│   │   └── routes/
│   │       ├── orders.py           # CRUD + stats
│   │       ├── inventory.py        # Products + alerts + adjustments
│   │       ├── agents.py           # Dispatch + task history + logs
│   │       ├── analytics.py        # Dashboard aggregations
│   │       └── documents.py        # Upload + semantic search
│   ├── agents/
│   │   ├── orchestrator.py         # Central task dispatcher
│   │   ├── document_processor.py   # 5-node LangGraph pipeline
│   │   ├── order_agent.py          # 6-node LangGraph pipeline
│   │   ├── inventory_agent.py      # 4-node LangGraph pipeline
│   │   └── migration_agent.py      # 4-node LangGraph pipeline
│   ├── services/
│   │   ├── vector_store.py         # Qdrant client
│   │   ├── llm_service.py          # OpenAI + Anthropic unified interface
│   │   └── telemetry.py            # OTel + W&B setup
│   ├── workers/
│   │   └── agent_worker.py         # Background task processor
│   └── dbt/
│       ├── dbt_project.yml
│       └── models/                 # 6 transformation models
│
├── frontend/
│   ├── src/
│   │   ├── App.tsx                 # Router + sidebar nav
│   │   ├── components/
│   │   │   ├── Dashboard.tsx       # Stats + charts
│   │   │   ├── AgentMonitor.tsx    # Dispatch + logs viewer
│   │   │   ├── OrderPanel.tsx      # Order management
│   │   │   ├── InventoryPanel.tsx  # Stock + alerts
│   │   │   ├── DocumentPanel.tsx   # Upload + search
│   │   │   └── MigrationPanel.tsx  # Legacy schema → modern
│   │   └── services/api.ts         # Axios API client
│
├── tests/
│   ├── test_agents.py              # Agent unit tests
│   ├── test_api.py                 # API integration tests
│   └── playwright/test_e2e.py      # Browser E2E tests
│
├── scripts/
│   ├── seed_data.py                # Database seeder
│   └── deploy.sh                   # One-command deployment
│
└── infra/
    ├── otel-collector-config.yml   # OTel pipeline config
    └── prometheus.yml              # Metrics scraping
```

---

## 🔑 Key Design Decisions

1. **LangGraph over simple chains** — Each agent is a directed graph with conditional routing, enabling complex business logic (e.g., auto-approve vs. escalate).

2. **Async everything** — SQLAlchemy async, FastAPI async, Redis async — designed for high throughput.

3. **pgvector + Qdrant dual vector strategy** — pgvector for transactional queries (products), Qdrant for document semantic search at scale.

4. **dbt for analytics** — Clean separation between operational data and analytics. Business users get `order_analytics`, `inventory_health`, and `agent_performance` marts.

5. **Full observability** — Every LLM call is traced. See exactly which agent step took how long, how many tokens, and what it cost.

6. **Background workers** — Agents can run synchronously (API response) or be queued for async processing via Redis.

---

## 📝 License

MIT — Built for the Modernization Strike Team.
