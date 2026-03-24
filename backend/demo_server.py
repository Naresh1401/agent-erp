"""
AgentERP Demo Server – standalone FastAPI app with in-memory data.

Runs without PostgreSQL, Redis, Qdrant, or LLM API keys.
Demonstrates the complete UI + API surface for live demos.

  cd agent-erp && python -m backend.demo_server
"""

from __future__ import annotations

import json
import os
import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

# ── Pydantic models ──────────────────────────────────────────

class OrderItemIn(BaseModel):
    product_id: str
    quantity: int
    unit_price: float

class OrderCreate(BaseModel):
    customer_id: str
    items: list[OrderItemIn]
    notes: str = ""

class AgentTaskRequest(BaseModel):
    agent_type: str
    input_data: dict[str, Any]

class DocumentUpload(BaseModel):
    filename: str
    raw_text: str

class DocumentSearch(BaseModel):
    query: str
    limit: int = 10

class ProductCreate(BaseModel):
    sku: str
    name: str
    description: str = ""
    category: str = "General"
    unit_price: float = 0.0
    cost_price: float = 0.0
    quantity_on_hand: int = 0
    reorder_point: int = 10

# ── In-memory data store ─────────────────────────────────────

def _id():
    return str(uuid.uuid4())

def _now():
    return datetime.utcnow().isoformat()

def _past(days: int):
    return (datetime.utcnow() - timedelta(days=days)).isoformat()

SUPPLIERS: list[dict] = []
PRODUCTS: list[dict] = []
CUSTOMERS: list[dict] = []
ORDERS: list[dict] = []
TASKS: list[dict] = []
DOCUMENTS: list[dict] = []

# ── Agent simulation functions ───────────────────────────────

def simulate_document_processor(input_data: dict) -> dict:
    filename = input_data.get("filename", "unknown")
    raw_text = input_data.get("raw_text", "")
    
    # Classify document
    doc_type = "invoice" if "invoice" in raw_text.lower() else "purchase_order" if "purchase order" in raw_text.lower() else "general"
    
    # Extract fields based on type
    fields = {}
    if doc_type == "invoice":
        fields = {
            "document_number": "INV-2024-001",
            "date": "2024-03-15",
            "vendor": "Acme Industrial Supply",
            "bill_to": "Widget Manufacturing Inc",
            "line_items": [
                {"description": "Industrial Bolt M8x40", "qty": 500, "unit_price": 0.45, "total": 225.00},
                {"description": "Steel Plate A36 12x12", "qty": 20, "unit_price": 89.99, "total": 1799.80},
                {"description": "Welding Wire ER70S-6", "qty": 10, "unit_price": 45.00, "total": 450.00},
            ],
            "subtotal": 2474.80,
            "tax_rate": 0.08,
            "tax_amount": 197.98,
            "shipping": 125.00,
            "total": 2797.78,
            "payment_terms": "Net 30",
        }
    elif doc_type == "purchase_order":
        fields = {
            "po_number": "PO-50234",
            "date": "2024-03-10",
            "vendor": "Pacific Steel Distributors",
            "ship_to": "Warehouse B - 456 Industrial Blvd",
            "line_items": [
                {"sku": "STEEL-HR-48", "description": "Hot Rolled Steel Sheet 4x8", "qty": 100, "unit_price": 156.00},
                {"sku": "ALUM-6061", "description": "Aluminum Bar 6061-T6", "qty": 50, "unit_price": 78.50},
                {"sku": "PIPE-SCH40", "description": "Steel Pipe Schedule 40", "qty": 200, "unit_price": 34.25},
            ],
            "total": 26175.00,
            "delivery_date": "2024-03-25",
        }
    
    steps = [
        {"name": "classify_document", "model": "gpt-4o", "tokens_in": 340, "tokens_out": 45, "duration_ms": 820},
        {"name": "extract_fields", "model": "gpt-4o", "tokens_in": 890, "tokens_out": 420, "duration_ms": 2340},
        {"name": "validate_extraction", "model": "gpt-4o", "tokens_in": 560, "tokens_out": 120, "duration_ms": 950},
        {"name": "generate_embedding", "model": "text-embedding-3-small", "tokens_in": 450, "tokens_out": 0, "duration_ms": 180},
    ]
    
    return {
        "doc_type": doc_type,
        "extracted_fields": fields,
        "validation_errors": [],
        "steps": steps,
        "tokens_used": sum(s["tokens_in"] + s["tokens_out"] for s in steps),
    }


def simulate_order_agent(input_data: dict) -> dict:
    order_data = input_data.get("order_data", {})
    customer = input_data.get("customer", {})
    items = order_data.get("items", [])
    
    subtotal = sum(i.get("quantity", 0) * i.get("unit_price", 0) for i in items)
    tax = round(subtotal * 0.08, 2)
    shipping = 0.0 if subtotal > 500 else 25.00
    total = round(subtotal + tax + shipping, 2)
    
    tier = customer.get("tier", "bronze")
    history = customer.get("order_history", 0)
    risk = "low" if tier in ("gold", "platinum") and history > 10 else "medium" if history > 5 else "high"
    decision = "approved" if risk in ("low", "medium") else "escalated"
    
    steps = [
        {"name": "validate_order", "model": None, "tokens_in": 0, "tokens_out": 0, "duration_ms": 12},
        {"name": "check_inventory", "model": None, "tokens_in": 0, "tokens_out": 0, "duration_ms": 45},
        {"name": "calculate_pricing", "model": None, "tokens_in": 0, "tokens_out": 0, "duration_ms": 8},
        {"name": "risk_assessment", "model": "gpt-4o", "tokens_in": 620, "tokens_out": 180, "duration_ms": 1200},
        {"name": "make_decision", "model": "gpt-4o", "tokens_in": 450, "tokens_out": 95, "duration_ms": 780},
        {"name": "finalize_order", "model": None, "tokens_in": 0, "tokens_out": 0, "duration_ms": 15},
    ]
    
    return {
        "order_summary": {
            "customer": customer.get("name", "Unknown"),
            "items_count": len(items),
            "subtotal": subtotal,
            "tax": tax,
            "shipping": shipping,
            "total": total,
        },
        "risk_assessment": {
            "risk_level": risk,
            "customer_tier": tier,
            "order_history": history,
            "factors": [
                f"Customer tier: {tier}",
                f"Order history: {history} previous orders",
                f"Order value: ${total:,.2f}",
            ],
        },
        "decision": decision,
        "reason": f"Order {decision} — {risk} risk customer ({tier} tier) with {history} previous orders. Total: ${total:,.2f}",
        "steps": steps,
        "tokens_used": sum(s["tokens_in"] + s["tokens_out"] for s in steps),
    }


def simulate_inventory_agent(input_data: dict) -> dict:
    products = input_data.get("products", [])
    
    stockouts = [p for p in products if p.get("quantity_on_hand", 0) == 0]
    low_stock = [p for p in products if 0 < p.get("quantity_on_hand", 0) <= p.get("reorder_point", 0)]
    overstock = [p for p in products if p.get("quantity_on_hand", 0) > p.get("reorder_point", 0) * 5]
    healthy = [p for p in products if p not in stockouts and p not in low_stock and p not in overstock]
    
    anomalies = []
    for p in stockouts:
        anomalies.append({"sku": p["sku"], "name": p["name"], "type": "stockout", "severity": "critical", "action": f"URGENT: Reorder {p['sku']} immediately"})
    for p in low_stock:
        deficit = p["reorder_point"] - p["quantity_on_hand"]
        anomalies.append({"sku": p["sku"], "name": p["name"], "type": "low_stock", "severity": "high", "action": f"Reorder {deficit}+ units of {p['sku']}"})
    for p in overstock:
        anomalies.append({"sku": p["sku"], "name": p["name"], "type": "overstock", "severity": "medium", "action": f"Consider reducing {p['sku']} — {p['quantity_on_hand']} units vs {p['reorder_point']} reorder point"})
    
    steps = [
        {"name": "analyze_stock_levels", "model": None, "tokens_in": 0, "tokens_out": 0, "duration_ms": 35},
        {"name": "detect_patterns", "model": "gpt-4o", "tokens_in": 980, "tokens_out": 450, "duration_ms": 2100},
        {"name": "forecast_demand", "model": "gpt-4o", "tokens_in": 1200, "tokens_out": 600, "duration_ms": 2800},
        {"name": "generate_summary", "model": "gpt-4o", "tokens_in": 750, "tokens_out": 380, "duration_ms": 1500},
    ]
    
    return {
        "summary": {
            "total_products": len(products),
            "stockouts": len(stockouts),
            "low_stock": len(low_stock),
            "overstock": len(overstock),
            "healthy": len(healthy),
        },
        "anomalies": anomalies,
        "forecast": {
            "analysis": "Based on current stock levels and historical patterns, 2 items require immediate attention. BOLT-M8 stockout is critical for production continuity. PLATE-A36 and WIDGET-A200 are at risk of stockout within 7 days at current consumption rates.",
            "recommendations": [
                "Place emergency order for NUT-M8 (currently at 0 units)",
                "Increase PLATE-A36 reorder quantity to 30 units",
                "Monitor WIDGET-A200 closely — 5 units remaining vs 25 reorder point",
                "Reduce CABLE-CAT6 standing order — 850 units significantly exceeds 50 reorder point",
            ],
        },
        "steps": steps,
        "tokens_used": sum(s["tokens_in"] + s["tokens_out"] for s in steps),
    }


def simulate_migration_agent(input_data: dict) -> dict:
    legacy_schema = input_data.get("legacy_schema", {})
    
    table_mappings = []
    for table, cols in legacy_schema.items():
        modern_name = {
            "tbl_cust": "customers",
            "tbl_item": "products", 
            "tbl_ord": "orders",
            "tbl_ord_dtl": "order_items",
            "tbl_vend": "suppliers",
        }.get(table, table.replace("tbl_", ""))
        
        col_mappings = {}
        for col, dtype in cols.items():
            modern_col = {
                "CUST_NO": "id (UUID)",
                "CUST_NM": "name",
                "CUST_ADDR": "address (JSONB with street, city, state, zip)",
                "CUST_PH": "phone",
                "CUST_EMAIL": "email",
                "CR_LMT": "credit_limit",
                "CUST_TYP": "customer_type (ENUM: retail, wholesale, enterprise)",
                "ACCT_BAL": "account_balance",
                "LST_ORD_DT": "last_order_date",
                "ITEM_NO": "id (UUID)",
                "ITEM_DESC": "name + description (split into two columns)",
                "ITEM_CAT": "category (expanded to full text ENUM)",
                "LIST_PRC": "unit_price",
                "COST": "cost_price",
                "QOH": "quantity_on_hand",
                "REORD_PT": "reorder_point",
                "REORD_QTY": "reorder_quantity",
                "VEND_NO": "supplier_id (UUID FK → suppliers)",
                "ORD_NO": "id (UUID)",
                "ORD_DT": "created_at (TIMESTAMPTZ)",
                "SHIP_DT": "shipped_at (TIMESTAMPTZ)",
                "ORD_TOT": "total_amount",
                "TAX_AMT": "tax_amount",
                "FRT_AMT": "shipping_amount",
                "ORD_STAT": "status (ENUM: draft, pending_review, approved, processing, shipped, delivered, cancelled, returned)",
                "SLSREP": "sales_rep_id (UUID FK → users, new table)",
                "LINE_NO": "id (UUID, auto-generated)",
                "QTY_ORD": "quantity",
                "QTY_SHIP": "quantity_shipped",
                "UNIT_PRC": "unit_price",
                "DISC_PCT": "discount_percent",
                "VEND_NM": "name",
                "VEND_ADDR": "address (JSONB)",
                "VEND_PH": "phone",
                "LEAD_TM": "lead_time_days",
            }.get(col, col.lower())
            col_mappings[col] = {"modern_name": modern_col, "original_type": dtype}
        
        table_mappings.append({
            "legacy_table": table,
            "modern_table": modern_name,
            "columns": col_mappings,
        })
    
    steps = [
        {"name": "analyze_legacy_schema", "model": "gpt-4o", "tokens_in": 1800, "tokens_out": 950, "duration_ms": 3200},
        {"name": "generate_column_mappings", "model": "gpt-4o", "tokens_in": 2400, "tokens_out": 1800, "duration_ms": 4500},
        {"name": "validate_transformations", "model": "gpt-4o", "tokens_in": 1200, "tokens_out": 600, "duration_ms": 2100},
        {"name": "create_migration_plan", "model": "gpt-4o", "tokens_in": 1500, "tokens_out": 1200, "duration_ms": 3800},
    ]
    
    return {
        "migration_plan": {
            "tables_analyzed": len(legacy_schema),
            "mappings": table_mappings,
            "breaking_changes": [
                "INT primary keys → UUID (requires surrogate key generation)",
                "CHAR(1) status codes → human-readable ENUMs",
                "VARCHAR address → structured JSONB",
                "DATETIME → TIMESTAMPTZ (timezone-aware)",
                "Implicit FK relationships → explicit UUID foreign keys",
            ],
            "new_features": [
                "pgvector columns on products for semantic search",
                "JSONB metadata columns for extensibility",
                "Automatic created_at/updated_at timestamps via triggers",
                "Full-text search indexes on name/description columns",
                "Audit trail via agent_tasks + agent_logs tables",
            ],
            "estimated_sql_statements": len(legacy_schema) * 3 + 10,
            "data_migration_steps": [
                "1. Create new schema with modern tables",
                "2. Generate UUID mapping tables for INT→UUID conversion",
                "3. Migrate tbl_vend → suppliers (no FK dependencies)",
                "4. Migrate tbl_cust → customers (no FK dependencies)",
                "5. Migrate tbl_item → products (FK: supplier_id)",
                "6. Migrate tbl_ord → orders (FK: customer_id)",
                "7. Migrate tbl_ord_dtl → order_items (FK: order_id, product_id)",
                "8. Validate row counts and referential integrity",
                "9. Generate embedding vectors for products",
                "10. Drop legacy tables and UUID mapping tables",
            ],
        },
        "steps": steps,
        "tokens_used": sum(s["tokens_in"] + s["tokens_out"] for s in steps),
    }


AGENT_HANDLERS = {
    "document_processor": simulate_document_processor,
    "order_agent": simulate_order_agent,
    "inventory_agent": simulate_inventory_agent,
    "migration_agent": simulate_migration_agent,
}

# ── FastAPI app ──────────────────────────────────────────────

app = FastAPI(
    title="AgentERP (Demo Mode)",
    description="AI-Powered ERP Modernization Platform – Demo / Local Development Server",
    version="1.0.0-demo",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "agent-erp", "version": "1.0.0-demo", "mode": "demo"}


@app.get("/")
async def root():
    # If frontend build exists, serve it; otherwise return API info
    index = FRONTEND_BUILD / "index.html"
    if index.is_file():
        return FileResponse(str(index))
    return {"service": "AgentERP", "docs": "/docs"}


# ── Seed Demo Data (step-by-step) ────────────────────────────

SEED_STEPS = ["suppliers", "products", "customers", "orders", "agent_tasks"]

@app.post("/api/v1/seed/{step}")
async def seed_step(step: str):
    """Seed one category at a time. Steps: suppliers, products, customers, orders, agent_tasks."""
    if step not in SEED_STEPS:
        raise HTTPException(status_code=400, detail=f"Unknown step: {step}. Valid: {SEED_STEPS}")

    if step == "suppliers":
        SUPPLIERS.clear()
        SUPPLIERS.extend([
            {"id": _id(), "name": "Acme Industrial Supply", "contact_email": "sales@acme.com", "phone": "214-555-0100", "lead_time_days": 5},
            {"id": _id(), "name": "Pacific Steel Distributors", "contact_email": "orders@pacsteel.com", "phone": "310-555-0200", "lead_time_days": 7},
            {"id": _id(), "name": "GlobalFast Electronics", "contact_email": "supply@gfe.com", "phone": "408-555-0300", "lead_time_days": 3},
            {"id": _id(), "name": "MidWest Fastener Co.", "contact_email": "info@mwfast.com", "phone": "312-555-0400", "lead_time_days": 4},
        ])
        return {"step": step, "count": len(SUPPLIERS)}

    if step == "products":
        PRODUCTS.clear()
        PRODUCTS.extend([
            {"id": _id(), "sku": "BOLT-M8", "name": "Industrial Bolt M8x40 Grade 8.8", "description": "Zinc-plated hex bolt", "category": "Fasteners", "unit_price": 0.45, "cost_price": 0.22, "quantity_on_hand": 12500, "reorder_point": 5000, "is_active": True},
            {"id": _id(), "sku": "BOLT-M10", "name": "Industrial Bolt M10x50 Grade 8.8", "description": "Zinc-plated hex bolt", "category": "Fasteners", "unit_price": 0.65, "cost_price": 0.32, "quantity_on_hand": 8400, "reorder_point": 3000, "is_active": True},
            {"id": _id(), "sku": "NUT-M8", "name": "Hex Nut M8 Grade 8", "description": "Zinc-plated hex nut", "category": "Fasteners", "unit_price": 0.15, "cost_price": 0.07, "quantity_on_hand": 0, "reorder_point": 5000, "is_active": True},
            {"id": _id(), "sku": "PLATE-A36", "name": "Steel Plate A36 12x12\"", "description": "Hot-rolled structural steel", "category": "Raw Materials", "unit_price": 89.99, "cost_price": 52.00, "quantity_on_hand": 15, "reorder_point": 20, "is_active": True},
            {"id": _id(), "sku": "PLATE-SS304", "name": "Stainless Steel Plate 304 4x8", "description": "Austenitic stainless steel", "category": "Raw Materials", "unit_price": 245.00, "cost_price": 165.00, "quantity_on_hand": 42, "reorder_point": 10, "is_active": True},
            {"id": _id(), "sku": "PIPE-SCH40", "name": "Steel Pipe Schedule 40 2\"", "description": "Carbon steel pipe", "category": "Raw Materials", "unit_price": 34.25, "cost_price": 18.50, "quantity_on_hand": 320, "reorder_point": 50, "is_active": True},
            {"id": _id(), "sku": "CABLE-CAT6", "name": "Cable Cat6 1000ft Plenum", "description": "UTP networking cable", "category": "Electronics", "unit_price": 125.00, "cost_price": 72.00, "quantity_on_hand": 850, "reorder_point": 50, "is_active": True},
            {"id": _id(), "sku": "CABLE-FIBER", "name": "Fiber Optic Cable OM3 500m", "description": "Multi-mode fiber optic cable", "category": "Electronics", "unit_price": 389.00, "cost_price": 210.00, "quantity_on_hand": 28, "reorder_point": 15, "is_active": True},
            {"id": _id(), "sku": "WIDGET-A200", "name": "Widget A-200 Assembly", "description": "Precision assembly unit", "category": "Assemblies", "unit_price": 340.00, "cost_price": 185.00, "quantity_on_hand": 5, "reorder_point": 25, "is_active": True},
            {"id": _id(), "sku": "WIDGET-B100", "name": "Widget B-100 Sub-Assembly", "description": "Component sub-assembly", "category": "Assemblies", "unit_price": 178.00, "cost_price": 95.00, "quantity_on_hand": 67, "reorder_point": 30, "is_active": True},
            {"id": _id(), "sku": "MOTOR-12V", "name": "DC Motor 12V 500RPM", "description": "Brushed DC motor", "category": "Electronics", "unit_price": 24.99, "cost_price": 12.50, "quantity_on_hand": 230, "reorder_point": 100, "is_active": True},
            {"id": _id(), "sku": "SENSOR-TEMP", "name": "Temperature Sensor PT100", "description": "RTD temperature sensor", "category": "Electronics", "unit_price": 45.00, "cost_price": 22.00, "quantity_on_hand": 180, "reorder_point": 75, "is_active": True},
            {"id": _id(), "sku": "WELD-ER70", "name": "Welding Wire ER70S-6 0.035\"", "description": "MIG welding wire", "category": "Consumables", "unit_price": 45.00, "cost_price": 28.00, "quantity_on_hand": 95, "reorder_point": 40, "is_active": True},
            {"id": _id(), "sku": "ALUM-6061", "name": "Aluminum Bar 6061-T6 1\"x3\"", "description": "Extruded aluminum bar", "category": "Raw Materials", "unit_price": 78.50, "cost_price": 42.00, "quantity_on_hand": 55, "reorder_point": 20, "is_active": True},
        ])
        return {"step": step, "count": len(PRODUCTS)}

    if step == "customers":
        CUSTOMERS.clear()
        CUSTOMERS.extend([
            {"id": _id(), "name": "Widget Manufacturing Inc", "email": "orders@widget.com", "tier": "gold"},
            {"id": _id(), "name": "TechParts Global", "email": "purchasing@techparts.com", "tier": "silver"},
            {"id": _id(), "name": "BuildRight Construction", "email": "materials@buildright.com", "tier": "gold"},
            {"id": _id(), "name": "Precision Dynamics", "email": "supply@precisiondyn.com", "tier": "platinum"},
            {"id": _id(), "name": "Metro Assembly Co", "email": "procurement@metroasm.com", "tier": "bronze"},
        ])
        return {"step": step, "count": len(CUSTOMERS)}

    if step == "orders":
        ORDERS.clear()
        statuses = ["draft", "pending_review", "approved", "processing", "shipped", "delivered", "cancelled", "returned"]
        for _ in range(25):
            status = random.choice(statuses)
            total = round(random.uniform(100, 15000), 2)
            tax = round(total * 0.08, 2)
            shipping = 0.0 if total > 500 else 25.00
            ORDERS.append({
                "id": _id(),
                "order_number": f"ORD-{random.randint(10000, 99999)}",
                "customer_id": random.choice(CUSTOMERS)["id"] if CUSTOMERS else _id(),
                "status": status,
                "total_amount": round(total + tax + shipping, 2),
                "tax_amount": tax,
                "shipping_amount": shipping,
                "source": random.choice(["manual", "agent", "agent", "api"]),
                "created_at": _past(random.randint(0, 60)),
            })
        return {"step": step, "count": len(ORDERS)}

    if step == "agent_tasks":
        TASKS.clear()
        agent_types = ["document_processor", "order_agent", "inventory_agent", "migration_agent"]
        for i in range(10):
            at = agent_types[i % 4]
            tokens = random.randint(800, 12000)
            TASKS.append({
                "id": _id(),
                "agent_type": at,
                "status": "completed",
                "input_data": {},
                "output_data": {"steps": [{"name": "step_1", "model": "gpt-4o", "tokens_in": tokens // 2, "tokens_out": tokens // 2, "duration_ms": random.randint(500, 4000)}]},
                "tokens_used": tokens,
                "cost_usd": round(tokens * 0.00002, 4),
                "started_at": _past(random.randint(0, 30)),
                "completed_at": _past(random.randint(0, 30)),
                "created_at": _past(random.randint(0, 30)),
                "error_message": None,
            })
        return {"step": step, "count": len(TASKS)}

@app.get("/api/v1/seed/steps")
async def seed_steps():
    """Return the ordered list of seed steps."""
    return {"steps": SEED_STEPS}


@app.post("/api/v1/reset")
async def reset_data():
    """Clear all data stores."""
    SUPPLIERS.clear()
    PRODUCTS.clear()
    CUSTOMERS.clear()
    ORDERS.clear()
    TASKS.clear()
    DOCUMENTS.clear()
    return {"message": "All data cleared"}


# ── Analytics ────────────────────────────────────────────────

@app.get("/api/v1/analytics/dashboard")
async def dashboard():
    # Aggregate order statuses
    status_counts: dict[str, int] = {}
    for o in ORDERS:
        status_counts[o["status"]] = status_counts.get(o["status"], 0) + 1

    recent_tasks = sorted(TASKS, key=lambda t: t["created_at"], reverse=True)[:10]

    # Dynamic anomalies computed from actual product data
    anomalies = []
    for p in PRODUCTS:
        if not p.get("is_active"):
            continue
        qty = p["quantity_on_hand"]
        rp = p["reorder_point"]
        if qty == 0:
            anomalies.append({"id": _id(), "type": "stockout", "severity": "critical", "entity_type": "product", "description": f"{p['sku']} out of stock — production at risk", "recommendation": "Place emergency order"})
        elif qty <= rp:
            anomalies.append({"id": _id(), "type": "low_stock", "severity": "high", "entity_type": "product", "description": f"{p['sku']} below reorder point ({qty} / {rp})", "recommendation": f"Order {rp - qty + 10}+ units"})
        elif qty > rp * 5:
            anomalies.append({"id": _id(), "type": "overstock", "severity": "medium", "entity_type": "product", "description": f"{p['sku']} overstocked ({qty} units, reorder at {rp})", "recommendation": "Reduce next PO quantity"})

    return {
        "total_orders": len(ORDERS),
        "total_products": len(PRODUCTS),
        "total_customers": len(CUSTOMERS),
        "total_agent_tasks": len(TASKS),
        "active_anomalies": len(anomalies),
        "orders_by_status": status_counts,
        "recent_agent_tasks": [
            {
                "id": t["id"],
                "agent_type": t["agent_type"],
                "status": t["status"],
                "created_at": t["created_at"],
                "tokens_used": t.get("tokens_used", 0),
                "cost_usd": round(t.get("tokens_used", 0) * 0.00002, 4),
            }
            for t in recent_tasks
        ],
        "top_anomalies": anomalies,
    }


# ── Orders ───────────────────────────────────────────────────

@app.get("/api/v1/orders/")
async def list_orders(status: Optional[str] = None, limit: int = 50, offset: int = 0):
    filtered = ORDERS if not status else [o for o in ORDERS if o["status"] == status]
    return sorted(filtered, key=lambda o: o["created_at"], reverse=True)[offset : offset + limit]


@app.get("/api/v1/orders/stats/summary")
async def order_stats():
    by_status: dict[str, int] = {}
    for o in ORDERS:
        by_status[o["status"]] = by_status.get(o["status"], 0) + 1
    return {"total": len(ORDERS), "by_status": by_status}


@app.post("/api/v1/orders/", status_code=201)
async def create_order(payload: OrderCreate):
    total = sum(i.quantity * i.unit_price for i in payload.items)
    tax = round(total * 0.08, 2)
    shipping = 0.0 if total > 500 else 25.00
    order = {
        "id": _id(),
        "order_number": f"ORD-{random.randint(10000, 99999)}",
        "customer_id": payload.customer_id,
        "status": "draft",
        "total_amount": round(total + tax + shipping, 2),
        "tax_amount": tax,
        "shipping_amount": shipping,
        "source": "manual",
        "created_at": _now(),
    }
    ORDERS.insert(0, order)
    return order


# ── Inventory ────────────────────────────────────────────────

@app.get("/api/v1/inventory/products")
async def list_products(category: Optional[str] = None, low_stock: bool = False, limit: int = 50, offset: int = 0):
    filtered = [p for p in PRODUCTS if p["is_active"]]
    if category:
        filtered = [p for p in filtered if p["category"] == category]
    if low_stock:
        filtered = [p for p in filtered if p["quantity_on_hand"] <= p["reorder_point"]]
    return filtered[offset : offset + limit]


@app.get("/api/v1/inventory/alerts")
async def low_stock_alerts():
    alerts = []
    for p in PRODUCTS:
        if p["is_active"] and p["quantity_on_hand"] <= p["reorder_point"]:
            alerts.append({
                "product_id": p["id"],
                "sku": p["sku"],
                "name": p["name"],
                "quantity_on_hand": p["quantity_on_hand"],
                "reorder_point": p["reorder_point"],
                "severity": "critical" if p["quantity_on_hand"] == 0 else "warning",
            })
    return sorted(alerts, key=lambda a: a["quantity_on_hand"])


@app.post("/api/v1/inventory/products", status_code=201)
async def create_product(payload: ProductCreate):
    product = {"id": _id(), **payload.model_dump(), "is_active": True}
    PRODUCTS.append(product)
    return product


@app.post("/api/v1/inventory/products/{product_id}/adjust")
async def adjust_inventory(product_id: str, quantity_change: int, reason: str = "manual_adjustment"):
    product = next((p for p in PRODUCTS if p["id"] == product_id), None)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    new_qty = product["quantity_on_hand"] + quantity_change
    if new_qty < 0:
        raise HTTPException(status_code=400, detail="Insufficient inventory")
    product["quantity_on_hand"] = new_qty
    return {"product_id": product_id, "new_quantity": new_qty}


# ── Agents ───────────────────────────────────────────────────

@app.post("/api/v1/agents/dispatch")
async def dispatch_agent(payload: AgentTaskRequest):
    handler = AGENT_HANDLERS.get(payload.agent_type)
    if not handler:
        raise HTTPException(status_code=400, detail=f"Unknown agent type: {payload.agent_type}")

    result = handler(payload.input_data)
    tokens = result.get("tokens_used", 0)

    task = {
        "id": _id(),
        "agent_type": payload.agent_type,
        "status": "completed",
        "input_data": payload.input_data,
        "output_data": result,
        "tokens_used": tokens,
        "cost_usd": round(tokens * 0.00002, 4),
        "started_at": _now(),
        "completed_at": _now(),
        "created_at": _now(),
        "error_message": None,
    }
    TASKS.insert(0, task)
    return task


@app.get("/api/v1/agents/tasks")
async def list_tasks(agent_type: Optional[str] = None, status: Optional[str] = None, limit: int = 50, offset: int = 0):
    filtered = TASKS
    if agent_type:
        filtered = [t for t in filtered if t["agent_type"] == agent_type]
    if status:
        filtered = [t for t in filtered if t["status"] == status]
    return filtered[offset : offset + limit]


@app.get("/api/v1/agents/tasks/{task_id}")
async def get_task(task_id: str):
    task = next((t for t in TASKS if t["id"] == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.get("/api/v1/agents/tasks/{task_id}/logs")
async def get_task_logs(task_id: str):
    task = next((t for t in TASKS if t["id"] == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    steps = task.get("output_data", {}).get("steps", [])
    return [
        {
            "step_name": step.get("name", f"step_{i}"),
            "step_order": i + 1,
            "llm_model": step.get("model"),
            "tokens_in": step.get("tokens_in", 0),
            "tokens_out": step.get("tokens_out", 0),
            "duration_ms": step.get("duration_ms", 0),
            "input_data": {},
            "output_data": {},
        }
        for i, step in enumerate(steps)
    ]


# ── Documents ────────────────────────────────────────────────

@app.post("/api/v1/documents/upload")
async def upload_document(payload: DocumentUpload):
    # Process document through simulated agent
    result = simulate_document_processor({"filename": payload.filename, "raw_text": payload.raw_text})

    doc = {
        "id": _id(),
        "filename": payload.filename,
        "raw_text": payload.raw_text,
        "doc_type": result["doc_type"],
        "extracted_fields": result["extracted_fields"],
        "created_at": _now(),
    }
    DOCUMENTS.insert(0, doc)

    # Also create an agent task record
    task = {
        "id": _id(),
        "agent_type": "document_processor",
        "status": "completed",
        "input_data": {"filename": payload.filename, "raw_text": payload.raw_text[:200]},
        "output_data": result,
        "tokens_used": result.get("tokens_used", 0),
        "cost_usd": round(result.get("tokens_used", 0) * 0.00002, 4),
        "started_at": _now(),
        "completed_at": _now(),
        "created_at": _now(),
        "error_message": None,
    }
    TASKS.insert(0, task)

    return {"document": doc, "extraction": result}


@app.post("/api/v1/documents/search")
async def search_documents(payload: DocumentSearch):
    # Simple keyword-based search (Qdrant would do semantic search in production)
    query_lower = payload.query.lower()
    results = []
    for doc in DOCUMENTS:
        text = doc.get("raw_text", "").lower()
        if query_lower in text or any(word in text for word in query_lower.split()):
            results.append({
                "score": round(random.uniform(0.75, 0.98), 3),
                "payload": {
                    "filename": doc["filename"],
                    "doc_type": doc["doc_type"],
                    "chunk": doc["raw_text"][:200],
                },
            })

    return {"results": results[: payload.limit]}


# ── Serve React static build (production) ───────────────────

FRONTEND_BUILD = Path(__file__).resolve().parent.parent / "frontend" / "build"

if FRONTEND_BUILD.is_dir():
    # Serve static assets (JS, CSS, images)
    app.mount("/static", StaticFiles(directory=str(FRONTEND_BUILD / "static")), name="static")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """Serve React SPA — any non-API route returns index.html."""
        file_path = FRONTEND_BUILD / full_path
        if full_path and file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(FRONTEND_BUILD / "index.html"))


# ── Entry point ──────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    print(f"\n🚀 AgentERP Demo Server starting on http://localhost:{port}")
    print(f"📖 API Docs: http://localhost:{port}/docs")
    print(f"🎨 Frontend: http://localhost:{port}\n")
    uvicorn.run(app, host="0.0.0.0", port=port)
