from datetime import datetime
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.orders.models import Order, OrderStatus, OrderItem
from src.products.models import Product
from src.shopping_cart.models import Cart


class OrderService:
    def __init__(self, db: AsyncSession, user_id: UUID):
        self.db = db
        self.user_id = user_id

    async def create_order_from_cart(self) -> Order:
        cart = await self.db.execute(
            select(Cart)
            .options(selectinload(Cart.items))
            .where(Cart.user_id == self.user_id)
        )
        cart = cart.scalars().first()

        if not cart or not cart.items:
            raise ValueError("Cart is empty")

        order = Order(user_id=self.user_id, status=OrderStatus.PENDING)
        self.db.add(order)
        await self.db.commit()
        await self.db.refresh(order)

        for item in cart.items:
            order_item = OrderItem(
                order_id=order.order_id,
                product_id=item.product_id,
                quantity=item.quantity
            )
            self.db.add(order_item)

            product = await self.db.execute(
                select(Product).where(Product.id == item.product_id)
            )
            product = product.scalars().first()

            if product.stock < item.quantity:
                raise ValueError(f"Not enough stock for product {product.name}")

            product.stock -= item.quantity

        await self.db.delete(cart)
        await self.db.commit()

        await self.db.refresh(order)
        return order

    async def update_order_status(self, order_id: UUID, new_status: OrderStatus) -> Order:
        query = (
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.order_id == order_id, Order.user_id == self.user_id)
        )
        result = await self.db.execute(query)
        order = result.scalars().first()

        if not order:
            raise ValueError("Order not found")

        if new_status == OrderStatus.CANCELLED:
            for item in order.items:
                product = await self.db.execute(select(Product).where(Product.id == item.product_id))
                product = product.scalars().first()
                product.stock += item.quantity

        order.status = new_status
        await self.db.commit()
        await self.db.refresh(order)
        return order


class SalesReportService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_sales_report(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None,
                               min_quantity: Optional[int] = None) -> List[OrderItem]:
        query = (
            select(OrderItem)
            .join(Order)
            .options(
                selectinload(OrderItem.product)
            )
        )

        if start_date:
            query = query.where(Order.created_at >= start_date)
        if end_date:
            query = query.where(Order.created_at <= end_date)
        if min_quantity:
            query = query.where(OrderItem.quantity >= min_quantity)

        result = await self.db.execute(query)
        order_items = result.scalars().all()

        return order_items
