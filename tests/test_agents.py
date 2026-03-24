"""Unit tests for agent pipelines."""

import pytest

from backend.agents.document_processor import build_document_processor_graph
from backend.agents.inventory_agent import build_inventory_agent_graph
from backend.agents.order_agent import build_order_agent_graph


class TestOrderAgent:
    """Test the order processing agent graph (without LLM calls for validation/pricing)."""

    def test_rejects_empty_order(self):
        graph = build_order_agent_graph()
        state = {
            "task_id": "test-1",
            "order_data": {"customer_id": "", "items": []},
            "customer": {},
            "line_items": [],
            "inventory_status": {},
            "pricing": {},
            "risk_assessment": {},
            "decision": "",
            "reason": "",
            "steps_completed": [],
            "error": "",
        }
        result = graph.invoke(state)
        assert result["decision"] == "rejected"
        assert "Missing customer_id" in result["error"] or "at least one item" in result["error"]

    def test_rejects_invalid_quantity(self):
        graph = build_order_agent_graph()
        state = {
            "task_id": "test-2",
            "order_data": {
                "customer_id": "c123",
                "items": [{"product_id": "p1", "quantity": 0, "unit_price": 10.0}],
            },
            "customer": {},
            "line_items": [],
            "inventory_status": {},
            "pricing": {},
            "risk_assessment": {},
            "decision": "",
            "reason": "",
            "steps_completed": [],
            "error": "",
        }
        result = graph.invoke(state)
        assert result["decision"] == "rejected"
        assert "invalid quantity" in result["error"]


class TestInventoryAgent:
    """Test inventory analysis (rule-based nodes, no LLM needed)."""

    def test_detects_stockout(self):
        graph = build_inventory_agent_graph()
        state = {
            "task_id": "test-inv-1",
            "products": [
                {"id": "1", "sku": "BOLT-M8", "name": "Bolt M8", "category": "Fasteners",
                 "quantity_on_hand": 0, "reorder_point": 100, "unit_price": 0.45},
            ],
            "anomalies": [],
            "forecast": {},
            "reorder_recommendations": [],
            "summary": "",
            "steps_completed": [],
            "error": "",
        }
        # Only run the first node (analyze_levels) to avoid LLM calls
        from backend.agents.inventory_agent import analyze_levels
        result = analyze_levels(state)
        assert len(result["anomalies"]) == 1
        assert result["anomalies"][0]["type"] == "stockout"
        assert result["anomalies"][0]["severity"] == "critical"

    def test_detects_low_stock(self):
        from backend.agents.inventory_agent import analyze_levels
        state = {
            "task_id": "test-inv-2",
            "products": [
                {"id": "2", "sku": "PLATE-A36", "name": "Steel Plate", "category": "Materials",
                 "quantity_on_hand": 5, "reorder_point": 20, "unit_price": 89.99},
            ],
            "anomalies": [],
            "forecast": {},
            "reorder_recommendations": [],
            "summary": "",
            "steps_completed": [],
            "error": "",
        }
        result = analyze_levels(state)
        assert len(result["anomalies"]) == 1
        assert result["anomalies"][0]["type"] == "low_stock"

    def test_detects_overstock(self):
        from backend.agents.inventory_agent import analyze_levels
        state = {
            "task_id": "test-inv-3",
            "products": [
                {"id": "3", "sku": "CABLE", "name": "Cable", "category": "Electronics",
                 "quantity_on_hand": 1000, "reorder_point": 50, "unit_price": 125.0},
            ],
            "anomalies": [],
            "forecast": {},
            "reorder_recommendations": [],
            "summary": "",
            "steps_completed": [],
            "error": "",
        }
        result = analyze_levels(state)
        assert len(result["anomalies"]) == 1
        assert result["anomalies"][0]["type"] == "overstock"

    def test_healthy_stock_no_anomalies(self):
        from backend.agents.inventory_agent import analyze_levels
        state = {
            "task_id": "test-inv-4",
            "products": [
                {"id": "4", "sku": "WIDGET", "name": "Widget", "category": "Assemblies",
                 "quantity_on_hand": 100, "reorder_point": 25, "unit_price": 50.0},
            ],
            "anomalies": [],
            "forecast": {},
            "reorder_recommendations": [],
            "summary": "",
            "steps_completed": [],
            "error": "",
        }
        result = analyze_levels(state)
        assert len(result["anomalies"]) == 0


class TestOrderPricing:
    """Test the pricing calculation node."""

    def test_pricing_calculation(self):
        from backend.agents.order_agent import calculate_pricing

        state = {
            "task_id": "test-price-1",
            "order_data": {
                "customer_id": "c123",
                "items": [
                    {"product_id": "p1", "quantity": 10, "unit_price": 100.0},
                    {"product_id": "p2", "quantity": 5, "unit_price": 50.0},
                ],
            },
            "customer": {},
            "line_items": [],
            "inventory_status": {},
            "pricing": {},
            "risk_assessment": {},
            "decision": "",
            "reason": "",
            "steps_completed": [],
            "error": "",
        }
        result = calculate_pricing(state)
        assert result["pricing"]["subtotal"] == 1250.0
        assert result["pricing"]["tax"] == 100.0  # 8%
        assert result["pricing"]["shipping"] == 0.0  # free over $500
        assert result["pricing"]["total"] == 1350.0

    def test_shipping_charged_under_500(self):
        from backend.agents.order_agent import calculate_pricing

        state = {
            "task_id": "test-price-2",
            "order_data": {
                "customer_id": "c123",
                "items": [{"product_id": "p1", "quantity": 1, "unit_price": 100.0}],
            },
            "customer": {},
            "line_items": [],
            "inventory_status": {},
            "pricing": {},
            "risk_assessment": {},
            "decision": "",
            "reason": "",
            "steps_completed": [],
            "error": "",
        }
        result = calculate_pricing(state)
        assert result["pricing"]["shipping"] == 25.0
