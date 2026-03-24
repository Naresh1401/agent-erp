"""Analytics & dashboard routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.schemas import AgentTaskDetail, DashboardStats
from backend.db.database import get_db
from backend.db.models import AgentTask, Anomaly, Customer, Order, Product

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/dashboard", response_model=DashboardStats)
async def dashboard(db: AsyncSession = Depends(get_db)):
    total_orders = (await db.execute(select(func.count(Order.id)))).scalar() or 0
    total_products = (await db.execute(select(func.count(Product.id)))).scalar() or 0
    total_customers = (await db.execute(select(func.count(Customer.id)))).scalar() or 0
    total_tasks = (await db.execute(select(func.count(AgentTask.id)))).scalar() or 0
    active_anomalies = (
        await db.execute(select(func.count(Anomaly.id)).where(Anomaly.is_resolved.is_(False)))
    ).scalar() or 0

    # Orders by status
    status_result = await db.execute(
        select(Order.status, func.count(Order.id)).group_by(Order.status)
    )
    orders_by_status = {row[0]: row[1] for row in status_result.all()}

    # Recent agent tasks
    recent_result = await db.execute(
        select(AgentTask).order_by(AgentTask.created_at.desc()).limit(10)
    )
    recent_tasks = recent_result.scalars().all()

    # Top anomalies
    anomaly_result = await db.execute(
        select(Anomaly)
        .where(Anomaly.is_resolved.is_(False))
        .order_by(Anomaly.created_at.desc())
        .limit(10)
    )
    top_anomalies = [
        {
            "id": str(a.id),
            "type": a.anomaly_type,
            "severity": a.severity,
            "entity_type": a.entity_type,
            "description": a.description,
            "recommendation": a.recommendation,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in anomaly_result.scalars().all()
    ]

    return DashboardStats(
        total_orders=total_orders,
        total_products=total_products,
        total_customers=total_customers,
        total_agent_tasks=total_tasks,
        active_anomalies=active_anomalies,
        orders_by_status=orders_by_status,
        recent_agent_tasks=recent_tasks,
        top_anomalies=top_anomalies,
    )
