from fastapi import APIRouter, Depends, HTTPException
from fastapi_pagination import Page
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID

from fastapi_cache.decorator import cache

from starlette import status

from src.database import get_db, custom_cache_key
from src.exceptions import ProductAlreadyExistsException
from src.products.schemas import ProductCreate, ProductUpdate, ProductResponse, ProductWithDiscountResponse
from src.products.services import ProductService, ProductDiscountService


product_router = APIRouter()


@product_router.get("/", response_model=Page[ProductWithDiscountResponse], status_code=status.HTTP_200_OK)
@cache(expire=60, key_builder=custom_cache_key)
async def list_products(
    db: AsyncSession = Depends(get_db),
    page: int = 1,
    size: int = 10
):
    service = ProductService(db)
    return await service.get_all_products_paginated(page=page, size=size)


@product_router.get("/filter/", response_model=Page[ProductWithDiscountResponse], status_code=status.HTTP_200_OK)
@cache(expire=60, key_builder=custom_cache_key)
async def filter_products(
    category_id: Optional[UUID] = None,
    subcategory_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    page: int = 1,
    size: int = 10
):
    service = ProductService(db)
    return await service.filter_products(category_id=category_id, subcategory_id=subcategory_id, page=page, size=size)


@product_router.put("/{product_id}/price/", response_model=ProductResponse, status_code=status.HTTP_200_OK)
async def update_product_price(
    product_id: UUID,
    new_price: float,
    db: AsyncSession = Depends(get_db)
):
    service = ProductService(db)
    return await service.update_product_price(product_id, new_price)


@product_router.post("/{product_id}/discount/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_discount(
    product_id: UUID,
    discount_percentage: int,
    db: AsyncSession = Depends(get_db)
):
    discount_service = ProductDiscountService(db)
    product_service = ProductService(db)
    await discount_service.create_discount(product_id, discount_percentage)
    return await product_service.get_product_by_id(product_id)


@product_router.delete("/{product_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    service = ProductService(db)
    return await service.delete_product(product_id)


@product_router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    body: ProductCreate,
    db: AsyncSession = Depends(get_db)
):
    service = ProductService(db)
    try:
        return await service.add_product(body)
    except ProductAlreadyExistsException as e:
        raise e


@product_router.put("/{product_id}/", response_model=ProductResponse, status_code=status.HTTP_200_OK)
async def update_product(
    product_id: UUID,
    body: ProductUpdate,
    db: AsyncSession = Depends(get_db)
):
    service = ProductService(db)
    updated_product = await service.update_product(product_id, body)
    return updated_product
