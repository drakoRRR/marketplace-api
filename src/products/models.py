import uuid

from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from src.database import Base
from src.mixin_models import TimestampMixin


class Product(Base, TimestampMixin):
    """Product model representing items in the store."""
    __tablename__ = "product"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(String, nullable=True)
    category_id = Column(UUID(as_uuid=True), ForeignKey("product_category.id"), nullable=False)
    category_rel = relationship("ProductCategory", back_populates="products")
    price = Column(Numeric(precision=10, scale=2))
    stock = Column(Integer, nullable=False)
    reserved = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)

    discounts = relationship("ProductDiscount", back_populates="product")

    @property
    def available_stock(self):
        return self.stock - self.reserved

    def __str__(self):
        return f"{self.name}, price:{self.price}"


class ProductCategory(Base, TimestampMixin):
    __tablename__ = "product_category"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(String, nullable=True)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("product_category.id"), nullable=True)

    parent = relationship("ProductCategory", remote_side=[id], back_populates="children")
    children = relationship("ProductCategory", back_populates="parent", cascade="all, delete-orphan")

    products = relationship("Product", back_populates="category_rel")

    @property
    def is_root(self):
        """Check if the category is a root category (has no parent)."""
        return self.parent_id is None

    def __str__(self):
        return f"{self.name}"


class ProductDiscount(Base, TimestampMixin):
    __tablename__ = "product_discount"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("product.id"), nullable=False)
    product = relationship("Product", back_populates="discounts")
    discount_percentage = Column(Integer, nullable=False)