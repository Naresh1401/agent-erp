"""Data Migration Agent – transforms legacy ERP schemas to modern data models.

LangGraph pipeline:
  1. Analyze legacy schema / data sample
  2. Map fields to modern schema via LLM
  3. Generate transformation rules
  4. Validate transformations
  5. Produce migration plan
"""

from __future__ import annotations

import json
import logging
from typing import Any, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph

from backend.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

llm = ChatOpenAI(model="gpt-4o", temperature=0, api_key=settings.openai_api_key)

MODERN_SCHEMA = {
    "customers": {
        "id": "UUID",
        "name": "VARCHAR(255)",
        "email": "VARCHAR(255)",
        "phone": "VARCHAR(50)",
        "company": "VARCHAR(255)",
        "address": "JSONB",
    },
    "products": {
        "id": "UUID",
        "sku": "VARCHAR(100)",
        "name": "VARCHAR(255)",
        "description": "TEXT",
        "category": "VARCHAR(100)",
        "unit_price": "NUMERIC(12,2)",
        "cost_price": "NUMERIC(12,2)",
        "quantity_on_hand": "INTEGER",
    },
    "orders": {
        "id": "UUID",
        "order_number": "VARCHAR(50)",
        "customer_id": "UUID FK→customers",
        "status": "ENUM(draft,pending_review,approved,...)",
        "total_amount": "NUMERIC(14,2)",
        "line_items": "order_items table (product_id, quantity, unit_price)",
    },
}


class MigrationState(TypedDict):
    task_id: str
    legacy_schema: dict[str, Any]
    legacy_sample_data: list[dict[str, Any]]
    field_mapping: dict[str, Any]
    transformation_rules: list[dict[str, Any]]
    validation_results: dict[str, Any]
    migration_plan: dict[str, Any]
    steps_completed: list[str]
    error: str


def analyze_legacy_schema(state: MigrationState) -> MigrationState:
    """Analyze the legacy schema and identify mapping opportunities."""
    messages = [
        SystemMessage(content=(
            "You are a database migration expert. Analyze the legacy schema and sample data, "
            "then produce a field mapping to this modern schema:\n"
            f"{json.dumps(MODERN_SCHEMA, indent=2)}\n\n"
            "Respond with JSON:\n"
            '{"mappings": [{"legacy_table": str, "legacy_field": str, "modern_table": str, '
            '"modern_field": str, "transformation": str, "confidence": float}], '
            '"unmapped_legacy_fields": [str], "notes": str}'
        )),
        HumanMessage(content=json.dumps({
            "legacy_schema": state["legacy_schema"],
            "sample_data": state["legacy_sample_data"][:5],
        }, indent=2)),
    ]

    response = llm.invoke(messages)
    try:
        mapping = json.loads(response.content.strip().removeprefix("```json").removesuffix("```").strip())
    except json.JSONDecodeError:
        mapping = {"mappings": [], "error": "Failed to parse mapping"}

    return {
        **state,
        "field_mapping": mapping,
        "steps_completed": [*state["steps_completed"], "analyze_schema"],
    }


def generate_transformations(state: MigrationState) -> MigrationState:
    """Generate SQL/Python transformation rules for each mapping."""
    messages = [
        SystemMessage(content=(
            "Based on these field mappings, generate transformation rules. "
            "For each mapping, produce a SQL expression or Python snippet that transforms the data.\n"
            "Respond with JSON:\n"
            '{"rules": [{"source": str, "target": str, "sql_expression": str, '
            '"python_expression": str, "notes": str}]}'
        )),
        HumanMessage(content=json.dumps(state["field_mapping"], indent=2)),
    ]

    response = llm.invoke(messages)
    try:
        rules = json.loads(response.content.strip().removeprefix("```json").removesuffix("```").strip())
    except json.JSONDecodeError:
        rules = {"rules": []}

    return {
        **state,
        "transformation_rules": rules.get("rules", []),
        "steps_completed": [*state["steps_completed"], "generate_transforms"],
    }


def validate_transformations(state: MigrationState) -> MigrationState:
    """Validate transformation rules against sample data."""
    messages = [
        SystemMessage(content=(
            "Validate these transformation rules against the sample data. "
            "Check for: data loss, type mismatches, null handling, edge cases.\n"
            "Respond with JSON:\n"
            '{"valid": bool, "issues": [{"rule_index": int, "issue": str, "severity": str}], '
            '"coverage_pct": float}'
        )),
        HumanMessage(content=json.dumps({
            "rules": state["transformation_rules"],
            "sample_data": state["legacy_sample_data"][:3],
        }, indent=2)),
    ]

    response = llm.invoke(messages)
    try:
        validation = json.loads(response.content.strip().removeprefix("```json").removesuffix("```").strip())
    except json.JSONDecodeError:
        validation = {"valid": False, "issues": [{"issue": "Validation parse failed"}]}

    return {
        **state,
        "validation_results": validation,
        "steps_completed": [*state["steps_completed"], "validate"],
    }


def create_migration_plan(state: MigrationState) -> MigrationState:
    """Create final migration execution plan."""
    total_mappings = len(state.get("field_mapping", {}).get("mappings", []))
    issues = state.get("validation_results", {}).get("issues", [])

    plan = {
        "status": "ready" if not issues else "needs_review",
        "total_field_mappings": total_mappings,
        "transformation_rules": len(state.get("transformation_rules", [])),
        "validation_issues": len(issues),
        "steps": [
            "1. Create staging tables",
            "2. Extract data from legacy system",
            "3. Apply transformations",
            "4. Validate transformed data",
            "5. Load into modern schema",
            "6. Verify data integrity",
            "7. Cutover",
        ],
        "estimated_tables": list(MODERN_SCHEMA.keys()),
    }

    return {
        **state,
        "migration_plan": plan,
        "steps_completed": [*state["steps_completed"], "plan"],
    }


# ── Build Graph ─────────────────────────────────────────────
def build_migration_agent_graph() -> StateGraph:
    graph = StateGraph(MigrationState)

    graph.add_node("analyze", analyze_legacy_schema)
    graph.add_node("transform", generate_transformations)
    graph.add_node("validate", validate_transformations)
    graph.add_node("plan", create_migration_plan)

    graph.set_entry_point("analyze")
    graph.add_edge("analyze", "transform")
    graph.add_edge("transform", "validate")
    graph.add_edge("validate", "plan")
    graph.add_edge("plan", END)

    return graph.compile()


migration_agent = build_migration_agent_graph()
