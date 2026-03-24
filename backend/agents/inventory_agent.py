"""Inventory Intelligence Agent – anomaly detection, demand forecasting, auto-reorder.

LangGraph pipeline:
  1. Analyze current inventory levels
  2. Detect anomalies (stockouts, overstock, unusual patterns)
  3. Generate demand forecast using LLM + historical data
  4. Produce reorder recommendations
  5. Create anomaly reports
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


class InventoryState(TypedDict):
    task_id: str
    products: list[dict[str, Any]]
    anomalies: list[dict[str, Any]]
    forecast: dict[str, Any]
    reorder_recommendations: list[dict[str, Any]]
    summary: str
    steps_completed: list[str]
    error: str


# ── Node Functions ──────────────────────────────────────────
def analyze_levels(state: InventoryState) -> InventoryState:
    """Analyze current inventory levels and flag items below reorder point."""
    anomalies = []
    for product in state["products"]:
        qty = product.get("quantity_on_hand", 0)
        reorder_pt = product.get("reorder_point", 10)

        if qty == 0:
            anomalies.append({
                "product_id": product["id"],
                "sku": product.get("sku"),
                "type": "stockout",
                "severity": "critical",
                "description": f"{product['name']} is out of stock",
                "current_qty": qty,
            })
        elif qty <= reorder_pt:
            anomalies.append({
                "product_id": product["id"],
                "sku": product.get("sku"),
                "type": "low_stock",
                "severity": "high",
                "description": f"{product['name']} below reorder point ({qty}/{reorder_pt})",
                "current_qty": qty,
            })
        elif qty > reorder_pt * 10:
            anomalies.append({
                "product_id": product["id"],
                "sku": product.get("sku"),
                "type": "overstock",
                "severity": "medium",
                "description": f"{product['name']} significantly overstocked ({qty} units, reorder at {reorder_pt})",
                "current_qty": qty,
            })

    return {
        **state,
        "anomalies": anomalies,
        "steps_completed": [*state["steps_completed"], "analyze_levels"],
    }


def detect_patterns(state: InventoryState) -> InventoryState:
    """Use LLM to detect unusual inventory patterns."""
    if not state["products"]:
        return {**state, "steps_completed": [*state["steps_completed"], "detect_patterns"]}

    product_summary = [
        {
            "sku": p.get("sku"),
            "name": p.get("name"),
            "category": p.get("category"),
            "qty": p.get("quantity_on_hand"),
            "reorder_point": p.get("reorder_point"),
            "unit_price": float(p.get("unit_price", 0)),
        }
        for p in state["products"][:50]  # limit to avoid token overflow
    ]

    messages = [
        SystemMessage(content=(
            "You are an inventory intelligence agent. Analyze the inventory data and identify:\n"
            "1. Unusual patterns across categories\n"
            "2. Products that may need attention\n"
            "3. Potential supply chain risks\n"
            "Respond with JSON: {\"patterns\": [{\"type\": str, \"description\": str, \"affected_skus\": [str], \"severity\": str}]}"
        )),
        HumanMessage(content=json.dumps(product_summary, indent=2)),
    ]

    response = llm.invoke(messages)
    try:
        patterns = json.loads(response.content.strip().removeprefix("```json").removesuffix("```").strip())
        for pattern in patterns.get("patterns", []):
            state["anomalies"].append({
                "type": pattern.get("type", "pattern"),
                "severity": pattern.get("severity", "medium"),
                "description": pattern.get("description", ""),
                "affected_skus": pattern.get("affected_skus", []),
            })
    except json.JSONDecodeError:
        logger.warning("Failed to parse LLM pattern detection response")

    return {**state, "steps_completed": [*state["steps_completed"], "detect_patterns"]}


def generate_forecast(state: InventoryState) -> InventoryState:
    """Generate demand forecast and reorder recommendations."""
    low_stock = [a for a in state["anomalies"] if a["type"] in ("stockout", "low_stock")]

    if not low_stock:
        return {
            **state,
            "forecast": {"status": "healthy", "message": "No immediate reorder needed"},
            "reorder_recommendations": [],
            "steps_completed": [*state["steps_completed"], "forecast"],
        }

    messages = [
        SystemMessage(content=(
            "You are a demand forecasting agent. Based on the low-stock alerts, "
            "generate reorder recommendations.\n"
            "Respond with JSON: {\"recommendations\": [{\"sku\": str, \"current_qty\": int, "
            "\"recommended_order_qty\": int, \"urgency\": \"immediate|soon|routine\", \"reason\": str}]}"
        )),
        HumanMessage(content=json.dumps(low_stock, indent=2)),
    ]

    response = llm.invoke(messages)
    try:
        result = json.loads(response.content.strip().removeprefix("```json").removesuffix("```").strip())
        recommendations = result.get("recommendations", [])
    except json.JSONDecodeError:
        recommendations = [
            {"sku": a.get("sku"), "recommended_order_qty": 50, "urgency": "immediate", "reason": a["description"]}
            for a in low_stock
        ]

    return {
        **state,
        "forecast": {"generated": True, "low_stock_count": len(low_stock)},
        "reorder_recommendations": recommendations,
        "steps_completed": [*state["steps_completed"], "forecast"],
    }


def generate_summary(state: InventoryState) -> InventoryState:
    """Generate executive summary of inventory health."""
    critical = len([a for a in state["anomalies"] if a.get("severity") == "critical"])
    high = len([a for a in state["anomalies"] if a.get("severity") == "high"])
    medium = len([a for a in state["anomalies"] if a.get("severity") == "medium"])
    reorders = len(state.get("reorder_recommendations", []))

    summary = (
        f"Inventory Health Report: {len(state['products'])} products analyzed. "
        f"Anomalies found: {critical} critical, {high} high, {medium} medium. "
        f"Reorder recommendations: {reorders}."
    )

    return {**state, "summary": summary, "steps_completed": [*state["steps_completed"], "summarize"]}


# ── Build Graph ─────────────────────────────────────────────
def build_inventory_agent_graph() -> StateGraph:
    graph = StateGraph(InventoryState)

    graph.add_node("analyze_levels", analyze_levels)
    graph.add_node("detect_patterns", detect_patterns)
    graph.add_node("forecast", generate_forecast)
    graph.add_node("summarize", generate_summary)

    graph.set_entry_point("analyze_levels")
    graph.add_edge("analyze_levels", "detect_patterns")
    graph.add_edge("detect_patterns", "forecast")
    graph.add_edge("forecast", "summarize")
    graph.add_edge("summarize", END)

    return graph.compile()


inventory_agent = build_inventory_agent_graph()
