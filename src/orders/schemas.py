from decimal import Decimal

from pydantic import BaseModel, computed_field
from uuid import UUID
from typing import List, Optional
from datetime import datetime

from src.orders.models import OrderStatus
from src.schemas import TunedModel


class OrderResponse(TunedModel):
    order_id: UUID
    user_id: UUID
    status: OrderStatus
    created_at: datetime
    updated_at: datetime


class ProductReportResponse(TunedModel):
    id: UUID
    name: str
    price: Decimal


class OrderItemResponse(TunedModel):
    order_item_id: UUID
    product: ProductReportResponse
    quantity: int

    @computed_field
    def total_price(self) -> Decimal:
        return self.quantity * self.product.price
