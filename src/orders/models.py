import uuid

from enum import Enum as PyEnum

from sqlalchemy import Column, String, Integer, Float, ForeignKey, DateTime, Enum as SQLAEnum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from src.database import Base
from src.mixin_models import TimestampMixin


class OrderStatus(str, PyEnum):
    PENDING = "pending"
    RESERVED = "reserved"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class Order(Base, TimestampMixin):
    """Order model representing orders in the store."""
    __tablename__ = "orders"

    order_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.user_id"), nullable=False)
    status = Column(SQLAEnum(OrderStatus, native_enum=False), default=OrderStatus.PENDING, nullable=False)

    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

    @property
    def total_amount(self):
        return self.items.aggregate(total_amount=func.sum(self.total_amount))["total_amount"]


class OrderItem(Base, TimestampMixin):
    """OrderItem model representing each item in an order."""
    __tablename__ = "order_items"

    order_item_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.order_id"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("product.id"), nullable=False)
    quantity = Column(Integer, nullable=False)

    order = relationship("Order", back_populates="items")
    product = relationship("Product")

    @property
    def item_total(self):
        return self.quantity * self.product.price

