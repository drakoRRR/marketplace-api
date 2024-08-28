from uuid import UUID
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class BaseProduct(BaseModel):

    class Config:
        from_attributes = True


class ProductDiscountResponse(BaseModel):
    id: UUID
    discount_percentage: int


class ProductCreate(BaseProduct):
    name: str
    description: Optional[str] = None
    category_id: UUID
    price: Decimal
    stock: int


class ProductUpdate(BaseProduct):
    name: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[UUID] = None
    price: Optional[Decimal] = None
    stock: Optional[int] = None
    is_active: Optional[bool] = None


class ProductResponse(ProductCreate):
    id: UUID


class ProductWithDiscountResponse(ProductCreate):
    discounts: Optional[list[ProductDiscountResponse]] = []
