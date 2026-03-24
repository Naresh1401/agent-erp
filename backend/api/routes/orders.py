"""Order management routes."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.api.schemas import OrderCreate, OrderOut
from backend.db.database import get_db
from backend.db.models import Order, OrderItem

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("/", response_model=list[OrderOut])
async def list_orders(
    status: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Order).order_by(Order.created_at.desc()).offset(offset).limit(limit)
    if status:
        stmt = stmt.where(Order.status == status)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{order_id}", response_model=OrderOut)
async def get_order(order_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Order).where(Order.id == order_id).options(selectinload(Order.items))
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.post("/", response_model=OrderOut, status_code=201)
async def create_order(payload: OrderCreate, db: AsyncSession = Depends(get_db)):
    order_number = f"ORD-{uuid.uuid4().hex[:8].upper()}"
    total = sum(item.quantity * item.unit_price for item in payload.items)
    tax = round(total * 0.08, 2)
    shipping = 0.0 if total > 500 else 25.00

    order = Order(
        order_number=order_number,
        customer_id=payload.customer_id,
        total_amount=round(total + tax + shipping, 2),
        tax_amount=tax,
        shipping_amount=shipping,
        notes=payload.notes,
        source="manual",
    )
    db.add(order)
    await db.flush()

    for item in payload.items:
        db.add(OrderItem(
            order_id=order.id,
            product_id=item.product_id,
            quantity=item.quantity,
            unit_price=item.unit_price,
        ))

    await db.flush()
    return order


@router.get("/stats/summary")
async def order_stats(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Order.status, func.count(Order.id)).group_by(Order.status)
    )
    by_status = {row[0]: row[1] for row in result.all()}
    total = sum(by_status.values())
    return {"total": total, "by_status": by_status}
