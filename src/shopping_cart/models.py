from sqlalchemy import Column, String, Integer, Float, ForeignKey, DateTime, Enum, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from src.database import Base
from src.mixin_models import TimestampMixin


class Cart(Base, TimestampMixin):
    """Cart model representing a shopping cart for users."""
    __tablename__ = "carts"

    cart_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.user_id"), nullable=False)

    user = relationship("User", back_populates="cart")
    items = relationship("CartItem", back_populates="cart", cascade="all, delete-orphan")

    @property
    def total_amount(self):
        return sum(item.item_total for item in self.items)


class CartItem(Base, TimestampMixin):
    """CartItem model representing each item in a cart."""
    __tablename__ = "cart_items"

    cart_item_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    cart_id = Column(UUID(as_uuid=True), ForeignKey("carts.cart_id"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("product.id"), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)

    cart = relationship("Cart", back_populates="items")
    product = relationship("Product")

    @property
    def item_total(self):
        return self.quantity * self.product.price
