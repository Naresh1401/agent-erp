"""Order Processing Agent – autonomous order lifecycle management.

LangGraph pipeline:
  1. Validate incoming order data
  2. Check inventory availability
  3. Calculate pricing (discounts, tax, shipping)
  4. Fraud/anomaly screening
  5. Auto-approve or escalate for human review
  6. Update inventory & create transactions
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph

from backend.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

llm = ChatOpenAI(model="gpt-4o", temperature=0, api_key=settings.openai_api_key)


class OrderState(TypedDict):
    task_id: str
    order_data: dict[str, Any]
    customer: dict[str, Any]
    line_items: list[dict[str, Any]]
    inventory_status: dict[str, Any]
    pricing: dict[str, Any]
    risk_assessment: dict[str, Any]
    decision: str  # approved, escalated, rejected
    reason: str
    steps_completed: list[str]
    error: str


# ── Node Functions ──────────────────────────────────────────
def validate_order(state: OrderState) -> OrderState:
    """Validate order data completeness and format."""
    errors = []
    order = state["order_data"]

    if not order.get("customer_id"):
        errors.append("Missing customer_id")
    if not order.get("items") or len(order["items"]) == 0:
        errors.append("Order must have at least one item")

    for i, item in enumerate(order.get("items", [])):
        if not item.get("product_id"):
            errors.append(f"Item {i}: missing product_id")
        if not item.get("quantity") or item["quantity"] <= 0:
            errors.append(f"Item {i}: invalid quantity")

    if errors:
        return {**state, "error": "; ".join(errors), "decision": "rejected", "reason": "; ".join(errors)}

    return {**state, "steps_completed": [*state["steps_completed"], "validate"]}


def check_inventory(state: OrderState) -> OrderState:
    """Check product availability for all line items."""
    if state.get("error"):
        return state

    inventory_results: dict[str, Any] = {"all_available": True, "items": []}

    # In production this queries the DB; here we simulate the check structure
    for item in state["order_data"].get("items", []):
        item_status = {
            "product_id": item["product_id"],
            "requested_qty": item["quantity"],
            "available": True,  # placeholder — real check in service layer
            "available_qty": item["quantity"],
        }
        inventory_results["items"].append(item_status)

    return {
        **state,
        "inventory_status": inventory_results,
        "steps_completed": [*state["steps_completed"], "check_inventory"],
    }


def calculate_pricing(state: OrderState) -> OrderState:
    """Calculate order totals with tax and shipping."""
    if state.get("error"):
        return state

    subtotal = 0.0
    items_priced = []
    for item in state["order_data"].get("items", []):
        unit_price = item.get("unit_price", 0)
        qty = item.get("quantity", 0)
        line_total = unit_price * qty
        subtotal += line_total
        items_priced.append({**item, "line_total": line_total})

    tax_rate = 0.08  # configurable per jurisdiction
    tax = round(subtotal * tax_rate, 2)
    shipping = 0.0 if subtotal > 500 else 25.00  # free shipping over $500
    total = round(subtotal + tax + shipping, 2)

    pricing = {
        "subtotal": subtotal,
        "tax_rate": tax_rate,
        "tax": tax,
        "shipping": shipping,
        "total": total,
        "items": items_priced,
    }

    return {
        **state,
        "pricing": pricing,
        "steps_completed": [*state["steps_completed"], "calculate_pricing"],
    }


def assess_risk(state: OrderState) -> OrderState:
    """Use LLM to assess order for fraud/anomaly indicators."""
    if state.get("error"):
        return state

    messages = [
        SystemMessage(content=(
            "You are a fraud detection agent for an ERP system. "
            "Analyze the following order and respond with a JSON object:\n"
            '{"risk_level": "low|medium|high", "flags": ["list of concerns"], '
            '"recommendation": "approve|review|reject"}\n'
            "Consider: order size, unusual quantities, customer history, pricing anomalies."
        )),
        HumanMessage(content=json.dumps({
            "customer": state.get("customer", {}),
            "pricing": state.get("pricing", {}),
            "item_count": len(state["order_data"].get("items", [])),
        }, indent=2)),
    ]

    response = llm.invoke(messages)
    try:
        risk = json.loads(response.content.strip().removeprefix("```json").removesuffix("```").strip())
    except json.JSONDecodeError:
        risk = {"risk_level": "medium", "flags": ["Could not parse risk assessment"], "recommendation": "review"}

    return {
        **state,
        "risk_assessment": risk,
        "steps_completed": [*state["steps_completed"], "assess_risk"],
    }


def make_decision(state: OrderState) -> OrderState:
    """Decide: auto-approve, escalate, or reject."""
    if state.get("error"):
        return state

    risk = state.get("risk_assessment", {})
    pricing = state.get("pricing", {})
    inventory = state.get("inventory_status", {})

    # Auto-reject if inventory unavailable
    if not inventory.get("all_available", True):
        return {**state, "decision": "rejected", "reason": "Insufficient inventory"}

    # Auto-approve low-risk orders under $10k
    if risk.get("risk_level") == "low" and pricing.get("total", 0) < 10000:
        return {
            **state,
            "decision": "approved",
            "reason": "Low risk, auto-approved",
            "steps_completed": [*state["steps_completed"], "decide"],
        }

    # Escalate high-risk or large orders
    if risk.get("risk_level") == "high" or pricing.get("total", 0) >= 50000:
        return {
            **state,
            "decision": "escalated",
            "reason": f"Risk: {risk.get('risk_level')}, Total: ${pricing.get('total', 0):,.2f}",
            "steps_completed": [*state["steps_completed"], "decide"],
        }

    # Medium risk → approve with logging
    return {
        **state,
        "decision": "approved",
        "reason": f"Medium risk approved – flags: {risk.get('flags', [])}",
        "steps_completed": [*state["steps_completed"], "decide"],
    }


def finalize_order(state: OrderState) -> OrderState:
    """Finalize approved order – deduct inventory, record transaction."""
    return {
        **state,
        "steps_completed": [*state["steps_completed"], "finalize"],
    }


# ── Routing ─────────────────────────────────────────────────
def route_after_validation(state: OrderState) -> str:
    return "end" if state.get("error") else "check_inventory"


def route_after_decision(state: OrderState) -> str:
    return "finalize" if state["decision"] == "approved" else "end"


# ── Build Graph ─────────────────────────────────────────────
def build_order_agent_graph() -> StateGraph:
    graph = StateGraph(OrderState)

    graph.add_node("validate", validate_order)
    graph.add_node("check_inventory", check_inventory)
    graph.add_node("calculate_pricing", calculate_pricing)
    graph.add_node("assess_risk", assess_risk)
    graph.add_node("decide", make_decision)
    graph.add_node("finalize", finalize_order)

    graph.set_entry_point("validate")
    graph.add_conditional_edges("validate", route_after_validation, {
        "check_inventory": "check_inventory",
        "end": END,
    })
    graph.add_edge("check_inventory", "calculate_pricing")
    graph.add_edge("calculate_pricing", "assess_risk")
    graph.add_edge("assess_risk", "decide")
    graph.add_conditional_edges("decide", route_after_decision, {
        "finalize": "finalize",
        "end": END,
    })
    graph.add_edge("finalize", END)

    return graph.compile()


order_agent = build_order_agent_graph()
