from pydantic import BaseModel
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

