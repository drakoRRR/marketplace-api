import time

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from src.auth.models import User
from src.products.models import ProductCategory, Product
from src.shopping_cart.models import CartItem, Cart
from tests.conftest import USER_NAME, PASSWORD


async def test_add_to_cart(client: AsyncClient, db_async_session: AsyncSession, user: User):
    response = await client.post(
        "/auth/login",
        data={"username": USER_NAME, "password": PASSWORD},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    access_token = response.json()["access"]

    category = ProductCategory(name="Electronics Game1")
    db_async_session.add(category)
    await db_async_session.commit()

    product = Product(
        name="Game Laptop",
        description="Gaming Laptop",
        category_id=category.id,
        price=1200.00,
        stock=10,
        is_active=True
    )
    db_async_session.add(product)
    await db_async_session.commit()

    response = await client.post(
        f"/cart/add/{product.id}",
        params={"quantity": 2},
        headers={"Authorization": f"Bearer {access_token}"}
    )

    assert response.status_code == status.HTTP_201_CREATED

    cart_item = await db_async_session.execute(select(CartItem).where(CartItem.product_id == product.id))
    cart_item = cart_item.scalars().first()

    assert cart_item is not None
    assert cart_item.quantity == 2


async def test_remove_from_cart(client: AsyncClient, db_async_session: AsyncSession, user: User):
    response = await client.post(
        "/auth/login",
        data={"username": USER_NAME, "password": PASSWORD},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    access_token = response.json()["access"]

    category = ProductCategory(name="Electronics Game2")
    db_async_session.add(category)
    await db_async_session.commit()

    product = Product(
        name="Laptop3",
        description="Gaming Laptop",
        category_id=category.id,
        price=1200.00,
        stock=10,
        is_active=True
    )
    db_async_session.add(product)
    await db_async_session.commit()

    cart = Cart(user_id=user.user_id)
    db_async_session.add(cart)
    await db_async_session.commit()

    cart_item = CartItem(
        cart_id=cart.cart_id,
        product_id=product.id,
        quantity=2
    )
    db_async_session.add(cart_item)
    await db_async_session.commit()

    response = await client.delete(f"/cart/remove/{product.id}",
                                   headers={"Authorization": f"Bearer {access_token}"})

    assert response.status_code == status.HTTP_204_NO_CONTENT

    cart_item = await db_async_session.execute(select(CartItem).where(CartItem.product_id == product.id))
    cart_item = cart_item.scalars().first()

    assert cart_item is None


async def test_update_cart_item(client: AsyncClient, db_async_session: AsyncSession, user: User):
    response = await client.post(
        "/auth/login",
        data={"username": USER_NAME, "password": PASSWORD},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    access_token = response.json()["access"]

    category = ProductCategory(name="Electronics4")
    db_async_session.add(category)
    await db_async_session.commit()

    product = Product(
        name="Laptop4",
        description="Gaming Laptop",
        category_id=category.id,
        price=1200.00,
        stock=10,
        is_active=True
    )
    db_async_session.add(product)
    await db_async_session.commit()

    cart = Cart(user_id=user.user_id)
    db_async_session.add(cart)
    await db_async_session.commit()

    cart_item = CartItem(
        cart_id=cart.cart_id,
        product_id=product.id,
        quantity=2
    )
    db_async_session.add(cart_item)
    await db_async_session.commit()
    #
    await db_async_session.refresh(product)

    response = await client.put(f"/cart/update/{product.id}", params={"quantity": 5},
                                headers={"Authorization": f"Bearer {access_token}"})

    assert response.status_code == status.HTTP_200_OK

    cart_item = await db_async_session.execute(select(CartItem).where(CartItem.product_id == product.id))
    cart_item = cart_item.scalars().first()

    await db_async_session.refresh(cart_item)

    assert cart_item is not None
    assert cart_item.quantity == 5
