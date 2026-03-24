"""Orchestrator – top-level agent that routes tasks to specialist agents."""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.models import AgentLog, AgentTask, Product

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """Central orchestrator that dispatches tasks to the right agent graph."""

    async def dispatch(self, agent_type: str, input_data: dict[str, Any], db: AsyncSession) -> dict[str, Any]:
        """Create a task record and run the appropriate agent."""
        task = AgentTask(
            agent_type=agent_type,
            status="running",
            input_data=input_data,
            started_at=datetime.utcnow(),
        )
        db.add(task)
        await db.flush()

        try:
            if agent_type == "document_processor":
                result = await self._run_document_processor(input_data, task.id, db)
            elif agent_type == "order_agent":
                result = await self._run_order_agent(input_data, task.id, db)
            elif agent_type == "inventory_agent":
                result = await self._run_inventory_agent(input_data, task.id, db)
            elif agent_type == "migration_agent":
                result = await self._run_migration_agent(input_data, task.id, db)
            else:
                raise ValueError(f"Unknown agent type: {agent_type}")

            task.status = "completed"
            task.output_data = result
            task.completed_at = datetime.utcnow()
            await db.flush()

            return {"task_id": str(task.id), "status": "completed", "result": result}

        except Exception as e:
            logger.exception(f"Agent {agent_type} failed: {e}")
            task.status = "failed"
            task.error_message = str(e)
            task.completed_at = datetime.utcnow()
            await db.flush()
            return {"task_id": str(task.id), "status": "failed", "error": str(e)}

    async def _run_document_processor(self, input_data: dict, task_id: uuid.UUID, db: AsyncSession) -> dict:
        from backend.agents.document_processor import document_processor

        initial_state = {
            "task_id": str(task_id),
            "filename": input_data.get("filename", "unknown"),
            "raw_text": input_data.get("raw_text", ""),
            "doc_type": "",
            "extracted_fields": {},
            "embedding": [],
            "validation_errors": [],
            "steps_completed": [],
            "error": "",
        }
        result = document_processor.invoke(initial_state)
        await self._log_steps(task_id, result.get("steps_completed", []), db)
        return {
            "doc_type": result.get("doc_type"),
            "extracted_fields": result.get("extracted_fields"),
            "validation_errors": result.get("validation_errors"),
            "steps": result.get("steps_completed"),
        }

    async def _run_order_agent(self, input_data: dict, task_id: uuid.UUID, db: AsyncSession) -> dict:
        from backend.agents.order_agent import order_agent

        initial_state = {
            "task_id": str(task_id),
            "order_data": input_data.get("order_data", {}),
            "customer": input_data.get("customer", {}),
            "line_items": [],
            "inventory_status": {},
            "pricing": {},
            "risk_assessment": {},
            "decision": "",
            "reason": "",
            "steps_completed": [],
            "error": "",
        }
        result = order_agent.invoke(initial_state)
        await self._log_steps(task_id, result.get("steps_completed", []), db)
        return {
            "decision": result.get("decision"),
            "reason": result.get("reason"),
            "pricing": result.get("pricing"),
            "risk_assessment": result.get("risk_assessment"),
            "steps": result.get("steps_completed"),
        }

    async def _run_inventory_agent(self, input_data: dict, task_id: uuid.UUID, db: AsyncSession) -> dict:
        from backend.agents.inventory_agent import inventory_agent

        # Fetch products from DB
        products_data = input_data.get("products", [])
        if not products_data:
            result_set = await db.execute(select(Product).where(Product.is_active.is_(True)).limit(200))
            products_orm = result_set.scalars().all()
            products_data = [
                {
                    "id": str(p.id),
                    "sku": p.sku,
                    "name": p.name,
                    "category": p.category,
                    "quantity_on_hand": p.quantity_on_hand,
                    "reorder_point": p.reorder_point,
                    "unit_price": float(p.unit_price),
                }
                for p in products_orm
            ]

        initial_state = {
            "task_id": str(task_id),
            "products": products_data,
            "anomalies": [],
            "forecast": {},
            "reorder_recommendations": [],
            "summary": "",
            "steps_completed": [],
            "error": "",
        }
        result = inventory_agent.invoke(initial_state)
        await self._log_steps(task_id, result.get("steps_completed", []), db)
        return {
            "anomalies": result.get("anomalies"),
            "forecast": result.get("forecast"),
            "reorder_recommendations": result.get("reorder_recommendations"),
            "summary": result.get("summary"),
            "steps": result.get("steps_completed"),
        }

    async def _run_migration_agent(self, input_data: dict, task_id: uuid.UUID, db: AsyncSession) -> dict:
        from backend.agents.migration_agent import migration_agent

        initial_state = {
            "task_id": str(task_id),
            "legacy_schema": input_data.get("legacy_schema", {}),
            "legacy_sample_data": input_data.get("legacy_sample_data", []),
            "field_mapping": {},
            "transformation_rules": [],
            "validation_results": {},
            "migration_plan": {},
            "steps_completed": [],
            "error": "",
        }
        result = migration_agent.invoke(initial_state)
        await self._log_steps(task_id, result.get("steps_completed", []), db)
        return {
            "field_mapping": result.get("field_mapping"),
            "transformation_rules": result.get("transformation_rules"),
            "validation_results": result.get("validation_results"),
            "migration_plan": result.get("migration_plan"),
            "steps": result.get("steps_completed"),
        }

    async def _log_steps(self, task_id: uuid.UUID, steps: list[str], db: AsyncSession) -> None:
        for i, step_name in enumerate(steps):
            log = AgentLog(task_id=task_id, step_name=step_name, step_order=i + 1)
            db.add(log)
        await db.flush()


orchestrator = AgentOrchestrator()
