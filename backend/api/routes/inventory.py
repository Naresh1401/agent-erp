"""Inventory management routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.schemas import ProductCreate, ProductOut
from backend.db.database import get_db
from backend.db.models import InventoryTransaction, Product

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.get("/products", response_model=list[ProductOut])
async def list_products(
    category: str | None = None,
    low_stock: bool = False,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Product).where(Product.is_active.is_(True)).offset(offset).limit(limit)
    if category:
        stmt = stmt.where(Product.category == category)
    if low_stock:
        stmt = stmt.where(Product.quantity_on_hand <= Product.reorder_point)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/products/{product_id}", response_model=ProductOut)
async def get_product(product_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.post("/products", response_model=ProductOut, status_code=201)
async def create_product(payload: ProductCreate, db: AsyncSession = Depends(get_db)):
    product = Product(**payload.model_dump())
    db.add(product)
    await db.flush()
    return product


@router.post("/products/{product_id}/adjust")
async def adjust_inventory(
    product_id: uuid.UUID,
    quantity_change: int,
    reason: str = "manual_adjustment",
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    new_qty = product.quantity_on_hand + quantity_change
    if new_qty < 0:
        raise HTTPException(status_code=400, detail="Insufficient inventory")

    product.quantity_on_hand = new_qty

    tx = InventoryTransaction(
        product_id=product_id,
        transaction_type="adjustment",
        quantity_change=quantity_change,
        reason=reason,
        performed_by="api",
    )
    db.add(tx)
    await db.flush()

    return {"product_id": str(product_id), "new_quantity": new_qty}


@router.get("/alerts")
async def low_stock_alerts(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Product)
        .where(Product.is_active.is_(True))
        .where(Product.quantity_on_hand <= Product.reorder_point)
        .order_by(Product.quantity_on_hand.asc())
    )
    products = result.scalars().all()
    return [
        {
            "product_id": str(p.id),
            "sku": p.sku,
            "name": p.name,
            "quantity_on_hand": p.quantity_on_hand,
            "reorder_point": p.reorder_point,
            "severity": "critical" if p.quantity_on_hand == 0 else "warning",
        }
        for p in products
    ]
