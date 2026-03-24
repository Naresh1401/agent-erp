"""Seed the database with realistic sample data for demos."""

import asyncio
import random
import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.database import async_session, engine
from backend.db.models import Base, Customer, Order, OrderItem, Product, Supplier


CATEGORIES = ["Fasteners", "Raw Materials", "Electronics", "Assemblies", "Tools", "Safety Equipment"]

PRODUCTS_DATA = [
    ("BOLT-M8X40", "Industrial Bolt M8x40 Grade 8.8", "Fasteners", 0.45, 0.22),
    ("BOLT-M10X60", "Industrial Bolt M10x60 Grade 10.9", "Fasteners", 0.89, 0.45),
    ("NUT-M8-NYL", "Nylon Lock Nut M8", "Fasteners", 0.12, 0.05),
    ("WASHER-M8-SS", "Flat Washer M8 Stainless", "Fasteners", 0.08, 0.03),
    ("PLATE-A36-12", "Steel Plate A36 12x12x0.5\"", "Raw Materials", 89.99, 52.00),
    ("PLATE-A36-24", "Steel Plate A36 24x24x0.5\"", "Raw Materials", 245.00, 142.00),
    ("PIPE-SCH40-2", "Steel Pipe Schedule 40 2\" x 10'", "Raw Materials", 34.25, 18.50),
    ("ALUM-6061-BAR", "Aluminum Bar 6061-T6 1\"x6'", "Raw Materials", 78.50, 45.00),
    ("CABLE-CAT6", "Cable Cat6 UTP 1000ft Box", "Electronics", 125.00, 72.00),
    ("CABLE-POWER-12", "Power Cable 12AWG 500ft", "Electronics", 189.00, 98.00),
    ("SWITCH-IND-24", "Industrial Ethernet Switch 24-port", "Electronics", 450.00, 280.00),
    ("SENSOR-PROX-M12", "Proximity Sensor M12 NPN", "Electronics", 67.50, 35.00),
    ("WIDGET-A200", "Widget Assembly A-200", "Assemblies", 340.00, 195.00),
    ("WIDGET-B100", "Widget Assembly B-100", "Assemblies", 215.00, 128.00),
    ("GEARBOX-RV40", "Planetary Gearbox RV40", "Assemblies", 895.00, 520.00),
    ("MOTOR-NEMA23", "Stepper Motor NEMA23 2.8A", "Assemblies", 42.00, 24.00),
    ("DRILL-HSS-SET", "HSS Drill Bit Set 1-13mm", "Tools", 156.00, 88.00),
    ("WRENCH-TORQUE", "Digital Torque Wrench 10-200 Nm", "Tools", 389.00, 225.00),
    ("CALIPER-DIG-6", "Digital Caliper 6\" Stainless", "Tools", 45.99, 22.00),
    ("GLOVE-NITRILE-L", "Nitrile Gloves Large Box/100", "Safety Equipment", 18.99, 8.50),
    ("GLASS-SAFETY-CLR", "Safety Glasses Clear Anti-Fog", "Safety Equipment", 12.50, 5.00),
    ("HELMET-HARD-WHT", "Hard Hat White Type I", "Safety Equipment", 24.99, 12.00),
]

CUSTOMERS_DATA = [
    ("Widget Manufacturing Inc", "orders@widgetmfg.com", "214-555-0100", "Widget Manufacturing"),
    ("Pacific Industrial Supply", "procurement@pacind.com", "415-555-0200", "Pacific Industrial"),
    ("Midwest Fabrication Co", "purchasing@midwestfab.com", "312-555-0300", "Midwest Fab"),
    ("Coastal Engineering Ltd", "buy@coastaleng.com", "619-555-0400", "Coastal Engineering"),
    ("Summit Machine Works", "orders@summitmw.com", "303-555-0500", "Summit Machine Works"),
    ("Valley Automation Inc", "supply@valleyauto.com", "602-555-0600", "Valley Automation"),
    ("Northern Steel Fabricators", "po@northsteel.com", "216-555-0700", "Northern Steel"),
    ("East Coast Assembly Co", "orders@ecassembly.com", "617-555-0800", "East Coast Assembly"),
]

SUPPLIERS_DATA = [
    ("Acme Industrial Supply", "sales@acmeindustrial.com", "800-555-1000", 5, 4.5),
    ("Pacific Steel Distributors", "orders@pacsteel.com", "888-555-2000", 7, 4.2),
    ("Global Fastener Corp", "supply@globalfast.com", "877-555-3000", 3, 4.8),
    ("TechParts International", "sales@techparts.com", "866-555-4000", 14, 3.9),
]


async def seed():
    async with async_session() as db:
        # Check if already seeded
        result = await db.execute(text("SELECT COUNT(*) FROM customers"))
        if result.scalar() > 0:
            print("Database already seeded – skipping")
            return

        # Suppliers
        suppliers = []
        for name, email, phone, lead_time, rating in SUPPLIERS_DATA:
            s = Supplier(name=name, email=email, phone=phone, lead_time_days=lead_time, rating=rating)
            db.add(s)
            suppliers.append(s)
        await db.flush()

        # Products
        products = []
        for sku, name, category, price, cost in PRODUCTS_DATA:
            supplier = random.choice(suppliers)
            qty = random.choice([0, 3, 8, 15, 50, 120, 300, 800, 1200])
            p = Product(
                sku=sku,
                name=name,
                category=category,
                unit_price=price,
                cost_price=cost,
                quantity_on_hand=qty,
                reorder_point=random.choice([10, 20, 50, 100]),
                reorder_quantity=random.choice([50, 100, 200, 500]),
                supplier_id=supplier.id,
            )
            db.add(p)
            products.append(p)
        await db.flush()

        # Customers
        customers = []
        for name, email, phone, company in CUSTOMERS_DATA:
            c = Customer(name=name, email=email, phone=phone, company=company)
            db.add(c)
            customers.append(c)
        await db.flush()

        # Orders
        statuses = ["draft", "pending_review", "approved", "processing", "shipped", "delivered", "cancelled"]
        sources = ["manual", "manual", "agent", "agent", "agent", "legacy_import"]

        for i in range(50):
            customer = random.choice(customers)
            num_items = random.randint(1, 5)
            order_products = random.sample(products, min(num_items, len(products)))

            order = Order(
                order_number=f"ORD-{uuid.uuid4().hex[:8].upper()}",
                customer_id=customer.id,
                status=random.choice(statuses),
                source=random.choice(sources),
            )
            db.add(order)
            await db.flush()

            total = 0.0
            for prod in order_products:
                qty = random.randint(1, 100)
                price = float(prod.unit_price)
                item = OrderItem(
                    order_id=order.id,
                    product_id=prod.id,
                    quantity=qty,
                    unit_price=price,
                )
                db.add(item)
                total += qty * price

            tax = round(total * 0.08, 2)
            shipping = 0.0 if total > 500 else 25.0
            order.total_amount = round(total + tax + shipping, 2)
            order.tax_amount = tax
            order.shipping_amount = shipping

        await db.commit()
        print(f"Seeded: {len(suppliers)} suppliers, {len(products)} products, {len(customers)} customers, 50 orders")


if __name__ == "__main__":
    asyncio.run(seed())
