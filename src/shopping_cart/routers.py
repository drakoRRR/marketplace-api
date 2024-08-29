from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from src.auth.models import User
from src.database import get_db
from src.shopping_cart.services import CartService
from src.auth.services import get_current_user


cart_router = APIRouter()


@cart_router.post("/add/{product_id}", status_code=status.HTTP_201_CREATED)
async def add_to_cart(
    product_id: UUID,
    quantity: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = CartService(db, current_user.user_id)
    return await service.add_product_to_cart(product_id, quantity)


@cart_router.delete("/remove/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_cart(
    product_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = CartService(db, current_user.user_id)
    await service.remove_product_from_cart(product_id)


@cart_router.put("/update/{product_id}", status_code=status.HTTP_200_OK)
async def update_cart_item(
    product_id: UUID,
    quantity: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = CartService(db, current_user.user_id)
    return await service.update_product_quantity(product_id, quantity)
