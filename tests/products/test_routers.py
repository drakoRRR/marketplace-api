import time
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import uuid4
from src.products.models import Product, ProductCategory, ProductDiscount
from src.products.schemas import ProductCreate, ProductUpdate
from fastapi import status


async def test_get_products(client: AsyncClient, db_async_session: AsyncSession):
    category = ProductCategory(id=uuid4(), name="Gaming Chairs")
    db_async_session.add(category)
    await db_async_session.commit()

    product = Product(
        name="Chair",
        description="Gaming",
        category_id=category.id,
        price=899.99,
        stock=20,
        is_active=True
    )
    db_async_session.add(product)
    await db_async_session.commit()

    response = await client.get("/products/", params={"size": 1, "page": 1})
    assert response.status_code == status.HTTP_200_OK

    response_json = response.json()

    assert "items" in response_json
    assert len(response_json["items"]) == 1
    assert response_json["items"][0]["name"] == "Chair"


async def test_update_product_price(client: AsyncClient, db_async_session: AsyncSession):
    category = ProductCategory(id=uuid4(), name="Electronics Machines")
    db_async_session.add(category)
    await db_async_session.commit()

    product = Product(
        name="Laptop",
        description="Gaming Laptop",
        category_id=category.id,
        price=1200.00,
        stock=10,
        is_active=True
    )
    db_async_session.add(product)
    await db_async_session.commit()

    new_price = Decimal("999.99")
    response = await client.put(f"/products/{product.id}/price/", params={"new_price": new_price})

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["price"] == str(new_price)

    stmt = select(Product).filter_by(id=product.id)
    result = await db_async_session.execute(stmt)
    updated_product = result.scalar_one_or_none()

    await db_async_session.refresh(updated_product)

    assert updated_product is not None
    assert updated_product.price == new_price


async def get_filtered_products(client: AsyncClient, db_async_session: AsyncSession):
    category1 = ProductCategory(id=uuid4(), name="Knifes")
    db_async_session.add(category1)
    await db_async_session.commit()

    category2 = ProductCategory(id=uuid4(), name="Milk")
    db_async_session.add(category2)
    await db_async_session.commit()

    product1 = Product(
        name="Knife",
        description="Knife",
        category_id=category1.id,
        price=899.99,
        stock=20,
        is_active=True
    )
    db_async_session.add(product1)

    product2 = Product(
        name="Milk",
        description="Milk",
        category_id=category2.id,
        price=899.99,
        stock=20,
        is_active=True
    )
    db_async_session.add(product2)

    response = await client.get("/products/filter/", params={"size": 1, "page": 1, "category_id": category1.id})
    assert response.status_code == status.HTTP_200_OK

    response_json = response.json()
    assert "items" in response_json
    assert len(response_json["items"]) == 1
    assert response_json["items"][0]["name"] == "Knife"

    response = await client.get("/products/filter/", params={"size": 1, "page": 1, "category_id": category2.id})
    assert response.status_code == status.HTTP_200_OK

    response_json = response.json()
    assert response_json["items"][0]["name"] == "Milk"


async def test_create_product(client: AsyncClient, db_async_session: AsyncSession):
    category = ProductCategory(name="Electronics")
    db_async_session.add(category)
    await db_async_session.commit()

    product_data = {
        "name": "Smartphone",
        "description": "Latest smartphone model",
        "category_id": str(category.id),
        "price": 799.99,
        "stock": 50,
        "is_active": True
    }

    response = await client.post("/products/", json=product_data)

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["name"] == product_data["name"]

    stmt = select(Product).filter_by(name=product_data["name"])
    result = await db_async_session.execute(stmt)
    product = result.scalar_one_or_none()

    assert product is not None
    assert product.name == product_data["name"]
    assert product.category_id == category.id


async def test_update_product(client: AsyncClient, db_async_session: AsyncSession):
    category = ProductCategory(name="Cars")
    db_async_session.add(category)
    await db_async_session.commit()

    product = Product(
        name="Laptop Acer",
        description="Monster laptop",
        category_id=category.id,
        price=1200.00,
        stock=20,
        is_active=True
    )
    db_async_session.add(product)
    await db_async_session.commit()

    update_data = {"description": "New description"}

    response = await client.put(f"/products/{product.id}/", json=update_data)

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["description"] == "New description"

    stmt = select(Product).where(Product.id == product.id)
    result = await db_async_session.execute(stmt)
    updated_product = result.scalar_one_or_none()

    await db_async_session.refresh(updated_product)

    assert updated_product is not None
    assert updated_product.description == update_data["description"]


async def test_delete_product(client: AsyncClient, db_async_session: AsyncSession):
    category = ProductCategory(name="Computers")
    db_async_session.add(category)
    await db_async_session.commit()

    product = Product(
        name="Tablet",
        description="Latest tablet model",
        category_id=category.id,
        price=500.00,
        stock=30,
        is_active=True
    )
    db_async_session.add(product)
    await db_async_session.commit()

    response = await client.delete(f"/products/{product.id}/")

    assert response.status_code == status.HTTP_204_NO_CONTENT

    stmt = select(Product).filter_by(id=product.id)
    result = await db_async_session.execute(stmt)
    deleted_product = result.scalar_one_or_none()

    assert deleted_product is None


async def test_create_discount(client: AsyncClient, db_async_session: AsyncSession):
    category = ProductCategory(name="Furniture")
    db_async_session.add(category)
    await db_async_session.commit()

    product = Product(
        name="Desk",
        description="Office Desk",
        category_id=category.id,
        price=200.00,
        stock=15,
        is_active=True
    )
    db_async_session.add(product)
    await db_async_session.commit()

    discount_percentage = 20
    response = await client.post(
        f"/products/{product.id}/discount/",
        params={"discount_percentage": discount_percentage}
    )

    assert response.status_code == status.HTTP_201_CREATED

    stmt = select(ProductDiscount).join(Product).filter(Product.id == product.id)
    result = await db_async_session.execute(stmt)
    discount = result.scalar_one_or_none()

    assert discount is not None
    assert discount.discount_percentage == discount_percentage
