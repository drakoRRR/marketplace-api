from uuid import UUID

from fastapi import Depends, HTTPException, APIRouter
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from src.auth.models import User
from src.auth.services import get_current_user
from src.database import get_db
from src.orders.models import OrderStatus
from src.orders.schemas import OrderResponse
from src.orders.services import OrderService


order_router = APIRouter()


@order_router.post("/create", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = OrderService(db, current_user.user_id)
    try:
        order = await service.create_order_from_cart()
        return order
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@order_router.put("/{order_id}/status", response_model=OrderResponse, status_code=status.HTTP_200_OK)
async def update_order_status(
    order_id: UUID,
    new_status: OrderStatus,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = OrderService(db, current_user.user_id)
    try:
        order = await service.update_order_status(order_id, new_status)
        return OrderResponse.from_orm(order)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
