"""Pydantic schemas shared across API routes."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


# ── Customer ────────────────────────────────────────────────
class CustomerCreate(BaseModel):
    name: str = Field(..., max_length=255)
    email: EmailStr
    phone: str | None = None
    company: str | None = None
    address: dict[str, Any] = {}


class CustomerOut(CustomerCreate):
    id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Product ─────────────────────────────────────────────────
class ProductCreate(BaseModel):
    sku: str = Field(..., max_length=100)
    name: str = Field(..., max_length=255)
    description: str | None = None
    category: str | None = None
    unit_price: float = Field(..., ge=0)
    cost_price: float | None = Field(None, ge=0)
    quantity_on_hand: int = Field(0, ge=0)
    reorder_point: int = 10
    reorder_quantity: int = 50
    supplier_id: UUID | None = None


class ProductOut(ProductCreate):
    id: UUID
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Order ───────────────────────────────────────────────────
class OrderItemCreate(BaseModel):
    product_id: UUID
    quantity: int = Field(..., gt=0)
    unit_price: float = Field(..., ge=0)


class OrderCreate(BaseModel):
    customer_id: UUID
    items: list[OrderItemCreate] = Field(..., min_length=1)
    notes: str | None = None


class OrderOut(BaseModel):
    id: UUID
    order_number: str
    customer_id: UUID
    status: str
    total_amount: float
    tax_amount: float
    shipping_amount: float
    source: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Agent ───────────────────────────────────────────────────
class AgentTaskRequest(BaseModel):
    agent_type: str = Field(..., pattern="^(document_processor|order_agent|inventory_agent|migration_agent)$")
    input_data: dict[str, Any] = {}


class AgentTaskOut(BaseModel):
    task_id: str
    status: str
    result: dict[str, Any] | None = None
    error: str | None = None


class AgentTaskDetail(BaseModel):
    id: UUID
    agent_type: str
    status: str
    input_data: dict[str, Any]
    output_data: dict[str, Any]
    error_message: str | None
    tokens_used: int
    cost_usd: float
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Document ────────────────────────────────────────────────
class DocumentUpload(BaseModel):
    filename: str
    raw_text: str


class DocumentOut(BaseModel):
    id: UUID
    filename: str
    status: str
    structured_data: dict[str, Any]
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Search ──────────────────────────────────────────────────
class SemanticSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    limit: int = Field(10, ge=1, le=100)


# ── Analytics ───────────────────────────────────────────────
class DashboardStats(BaseModel):
    total_orders: int
    total_products: int
    total_customers: int
    total_agent_tasks: int
    active_anomalies: int
    orders_by_status: dict[str, int]
    recent_agent_tasks: list[AgentTaskDetail]
    top_anomalies: list[dict[str, Any]]
