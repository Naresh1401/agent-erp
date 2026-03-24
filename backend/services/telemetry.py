"""OpenTelemetry + Weights & Biases observability setup."""

from __future__ import annotations

import logging

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from backend.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def setup_telemetry(app) -> None:
    """Initialize OpenTelemetry tracing and instrument FastAPI."""
    resource = Resource.create({"service.name": settings.otel_service_name})
    provider = TracerProvider(resource=resource)

    otlp_exporter = OTLPSpanExporter(endpoint=settings.otel_exporter_otlp_endpoint, insecure=True)
    provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

    trace.set_tracer_provider(provider)
    FastAPIInstrumentor.instrument_app(app)

    logger.info(f"Telemetry initialized → {settings.otel_exporter_otlp_endpoint}")


def get_tracer(name: str = "agent-erp"):
    return trace.get_tracer(name)


def setup_wandb() -> None:
    """Initialize Weights & Biases for experiment tracking."""
    if not settings.wandb_api_key:
        logger.info("W&B not configured – skipping")
        return

    try:
        import wandb
        wandb.init(project=settings.wandb_project, config={"service": settings.otel_service_name})
        logger.info(f"W&B initialized → project={settings.wandb_project}")
    except Exception as e:
        logger.warning(f"W&B init failed: {e}")


def log_agent_metrics(agent_type: str, duration_ms: int, tokens: int, cost: float, success: bool) -> None:
    """Log agent execution metrics to W&B."""
    try:
        import wandb
        if wandb.run:
            wandb.log({
                f"agent/{agent_type}/duration_ms": duration_ms,
                f"agent/{agent_type}/tokens": tokens,
                f"agent/{agent_type}/cost_usd": cost,
                f"agent/{agent_type}/success": int(success),
            })
    except Exception:
        pass
