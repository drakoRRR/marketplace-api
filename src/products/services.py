from decimal import Decimal

from fastapi_pagination import Page, Params
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from uuid import UUID
from typing import List, Optional

from src.exceptions import ProductAlreadyExistsException
from src.products.models import Product, ProductCategory, ProductDiscount
from src.products.schemas import ProductCreate, ProductUpdate, ProductWithDiscountResponse


class ProductService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_data_pagination(self, page: int, size: int, query) -> Page:
        products = await self.db.execute(query)
        products = [product for product in products.scalars().all() if product.available_stock > 0]

        params = Params(page=page, size=size)

        total = len(products)
        start = (params.page - 1) * params.size
        end = start + params.size
        paginated_items = products[start:end]

        for product in paginated_items:
            await ProductDiscountService(self.db).apply_discount(product)

        return Page.create(paginated_items, total=total, params=params)

    async def get_all_products_paginated(self, page: int = 1, size: int = 10) -> Page[Product]:
        """Getting a page with active products with discounts taken into account and available stock."""
        query = select(Product).where(
            Product.is_active == True
        ).options(selectinload(Product.discounts))

        paginated_result = await self._get_data_pagination(page, size, query)
        paginated_result.items = [ProductWithDiscountResponse.from_orm(product) for product in paginated_result.items]
        return paginated_result

    async def filter_products(self, category_id: Optional[UUID] = None, subcategory_id: Optional[UUID] = None,
                              page: int = 1, size: int = 10) -> Page[Product]:
        """Product filtering by category and subcategory."""
        query = select(Product).where(Product.is_active == True).options(selectinload(Product.discounts))

        if category_id:
            query = query.where(Product.category_id == category_id)

        if subcategory_id:
            query = query.join(ProductCategory, Product.category_rel).where(ProductCategory.parent_id == subcategory_id)

        paginated_result = await self._get_data_pagination(page, size, query)
        paginated_result.items = [ProductWithDiscountResponse.from_orm(product) for product in paginated_result.items]
        return paginated_result

    async def add_product(self, product_data: ProductCreate) -> Product:
        """Adding a new product with a check for existing products."""
        # Проверяем, существует ли продукт с таким же именем
        query = select(Product).where(Product.name == product_data.name)
        result = await self.db.execute(query)
        existing_product = result.scalars().first()

        if existing_product:
            raise ProductAlreadyExistsException()

        new_product = Product(**product_data.dict())
        self.db.add(new_product)
        await self.db.commit()
        await self.db.refresh(new_product)
        return new_product

    async def update_product_price(self, product_id: UUID, new_price: float) -> Product:
        """Product price update."""
        query = select(Product).where(Product.id == product_id)
        result = await self.db.execute(query)
        product = result.scalars().first()
        if not product:
            raise ValueError("Product not found")
        product.price = new_price
        await self.db.commit()
        await self.db.refresh(product)
        return product

    async def delete_product(self, product_id: UUID) -> None:
        """Product delete."""
        query = select(Product).where(Product.id == product_id)
        result = await self.db.execute(query)
        product = result.scalars().one_or_none()

        if product is None:
            raise NoResultFound(f"Product with ID {product_id} not found.")

        await self.db.delete(product)
        await self.db.commit()

    async def get_product_by_id(self, product_id: UUID) -> Product:
        """Receiving the product by its ID, taking into account the discount."""
        query = select(Product).where(Product.id == product_id).options(selectinload(Product.discounts))
        result = await self.db.execute(query)
        product = result.scalars().one_or_none()

        if product is None:
            raise NoResultFound(f"Product with ID {product_id} not found.")

        await ProductDiscountService(self.db).apply_discount(product)

        return product

    async def update_product(self, product_id: UUID, product_data: ProductUpdate) -> Product:
        """Update an existing product."""
        query = select(Product).where(Product.id == product_id)
        result = await self.db.execute(query)
        product = result.scalars().first()

        if not product:
            raise ValueError("Product not found")

        for field, value in product_data.dict(exclude_unset=True).items():
            setattr(product, field, value)

        await self.db.commit()
        await self.db.refresh(product)
        return product


class ProductDiscountService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_discount(self, product_id: UUID, discount_percentage: int) -> ProductDiscount:
        """Creation of a discount on a product."""
        query = select(Product).where(Product.id == product_id)
        result = await self.db.execute(query)
        product = result.scalars().first()

        if not product:
            raise ValueError("Product not found")

        discount = ProductDiscount(product_id=product_id, discount_percentage=discount_percentage)
        self.db.add(discount)
        await self.db.commit()
        await self.db.refresh(discount)
        return discount

    @staticmethod
    async def apply_discount(product: Product) -> None:
        """Applying a discount to the product."""
        if product.discounts:
            latest_discount = max(product.discounts, key=lambda d: d.created_at)
            discount_multiplier = Decimal(1) - Decimal(latest_discount.discount_percentage) / Decimal(100)
            product.price = product.price * discount_multiplier
