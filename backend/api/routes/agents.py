"""Agent management routes – dispatch tasks, view results, monitor agents."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.agents.orchestrator import orchestrator
from backend.api.schemas import AgentTaskDetail, AgentTaskOut, AgentTaskRequest
from backend.db.database import get_db
from backend.db.models import AgentTask

router = APIRouter(prefix="/agents", tags=["agents"])


@router.post("/dispatch", response_model=AgentTaskOut)
async def dispatch_agent(payload: AgentTaskRequest, db: AsyncSession = Depends(get_db)):
    """Dispatch a task to an autonomous agent."""
    result = await orchestrator.dispatch(payload.agent_type, payload.input_data, db)
    return AgentTaskOut(**result)


@router.get("/tasks", response_model=list[AgentTaskDetail])
async def list_tasks(
    agent_type: str | None = None,
    status: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(AgentTask).order_by(AgentTask.created_at.desc()).offset(offset).limit(limit)
    if agent_type:
        stmt = stmt.where(AgentTask.agent_type == agent_type)
    if status:
        stmt = stmt.where(AgentTask.status == status)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/tasks/{task_id}", response_model=AgentTaskDetail)
async def get_task(task_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(AgentTask).where(AgentTask.id == task_id).options(selectinload(AgentTask.logs))
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.get("/tasks/{task_id}/logs")
async def get_task_logs(task_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(AgentTask).where(AgentTask.id == task_id).options(selectinload(AgentTask.logs))
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return [
        {
            "step_name": log.step_name,
            "step_order": log.step_order,
            "input_data": log.input_data,
            "output_data": log.output_data,
            "llm_model": log.llm_model,
            "tokens_in": log.tokens_in,
            "tokens_out": log.tokens_out,
            "duration_ms": log.duration_ms,
        }
        for log in sorted(task.logs, key=lambda l: l.step_order)
    ]
