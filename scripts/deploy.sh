#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# AgentERP – Deployment Script
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

echo "╔══════════════════════════════════════════╗"
echo "║       AgentERP – Deployment Script       ║"
echo "╚══════════════════════════════════════════╝"

# ── 1. Check prerequisites ──────────────────────────────────
echo ""
echo "▶ Checking prerequisites..."

for cmd in docker docker-compose; do
    if ! command -v "$cmd" &>/dev/null; then
        echo "❌ $cmd is required but not installed."
        exit 1
    fi
done
echo "  ✓ Docker and Docker Compose available"

# ── 2. Environment file ─────────────────────────────────────
if [ ! -f .env ]; then
    echo ""
    echo "▶ Creating .env from .env.example..."
    cp .env.example .env
    echo "  ⚠ Edit .env with your API keys before running agents!"
fi

# ── 3. Build & start services ───────────────────────────────
echo ""
echo "▶ Building and starting all services..."
docker-compose build --parallel
docker-compose up -d

# ── 4. Wait for Postgres ────────────────────────────────────
echo ""
echo "▶ Waiting for PostgreSQL..."
for i in $(seq 1 30); do
    if docker-compose exec -T postgres pg_isready -U erp_admin &>/dev/null; then
        echo "  ✓ PostgreSQL is ready"
        break
    fi
    sleep 1
done

# ── 5. Seed database ────────────────────────────────────────
echo ""
echo "▶ Seeding database with sample data..."
docker-compose exec -T backend python -m scripts.seed_data

# ── 6. Display status ───────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════╗"
echo "║          🚀 AgentERP is LIVE!            ║"
echo "╠══════════════════════════════════════════╣"
echo "║                                          ║"
echo "║  Frontend:    http://localhost:3000       ║"
echo "║  API Docs:    http://localhost:8000/docs  ║"
echo "║  API Health:  http://localhost:8000/health║"
echo "║  Jaeger UI:   http://localhost:16686      ║"
echo "║  Grafana:     http://localhost:3001       ║"
echo "║  Prometheus:  http://localhost:9090       ║"
echo "║                                          ║"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "📌 Next steps:"
echo "  1. Add your OpenAI/Anthropic API keys to .env"
echo "  2. Restart: docker-compose restart backend agent-worker"
echo "  3. Open http://localhost:3000 and try the Agent Monitor"
echo ""
