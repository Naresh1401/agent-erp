"""AgentERP – FastAPI application entry point."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import agents, analytics, documents, inventory, orders
from backend.config import get_settings
from backend.services.telemetry import setup_telemetry, setup_wandb

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("AgentERP starting up…")
    setup_wandb()
    yield
    logger.info("AgentERP shutting down…")


app = FastAPI(
    title="AgentERP",
    description="AI-Powered ERP Modernization Platform – autonomous agents for enterprise operations",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Telemetry ───────────────────────────────────────────────
setup_telemetry(app)

# ── Routes ──────────────────────────────────────────────────
app.include_router(orders.router, prefix="/api/v1")
app.include_router(inventory.router, prefix="/api/v1")
app.include_router(agents.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "agent-erp", "version": "1.0.0"}


@app.get("/")
async def root():
    return {
        "message": "AgentERP – AI-Powered ERP Modernization Platform",
        "docs": "/docs",
        "health": "/health",
    }
