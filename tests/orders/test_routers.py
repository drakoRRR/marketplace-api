from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from src.auth.models import User
from src.orders.models import Order, OrderStatus, OrderItem
from src.products.models import ProductCategory, Product
from src.shopping_cart.models import Cart, CartItem
from tests.conftest import USER_NAME, PASSWORD


async def test_create_order(client: AsyncClient, db_async_session: AsyncSession, user: User):
    response = await client.post(
        "/auth/login",
        data={"username": USER_NAME, "password": PASSWORD},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    access_token = response.json()["access"]

    category = ProductCategory(name="Electronics Entertainment")
    db_async_session.add(category)
    await db_async_session.commit()

    product = Product(
        name="Laptop Monster",
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
        quantity=1
    )
    db_async_session.add(cart_item)
    await db_async_session.commit()

    response = await client.post("/order/create", headers={"Authorization": f"Bearer {access_token}"})
    print(response.json())

    assert response.status_code == status.HTTP_201_CREATED

    order_response = response.json()
    assert order_response["user_id"] == str(user.user_id)


async def test_update_order_status(client: AsyncClient, db_async_session: AsyncSession, user: User):
    response = await client.post(
        "/auth/login",
        data={"username": USER_NAME, "password": PASSWORD},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    access_token = response.json()["access"]

    category = ProductCategory(name="Electronics Good")
    db_async_session.add(category)
    await db_async_session.commit()

    product = Product(
        name="Laptop Monsters",
        description="Gaming Laptop",
        category_id=category.id,
        price=1200.00,
        stock=10,
        is_active=True
    )
    db_async_session.add(product)
    await db_async_session.commit()

    order = Order(user_id=user.user_id, status=OrderStatus.PENDING)
    db_async_session.add(order)
    await db_async_session.commit()

    order_item = OrderItem(
        order_id=order.order_id,
        product_id=product.id,
        quantity=1
    )
    db_async_session.add(order_item)
    await db_async_session.commit()

    new_status = OrderStatus.COMPLETED
    response = await client.put(f"/order/{order.order_id}/status", params={"new_status": new_status.value},
                                headers={"Authorization": f"Bearer {access_token}"})

    assert response.status_code == status.HTTP_200_OK

    order_response = response.json()
    assert order_response["status"] == new_status.value


async def test_sales_report(client: AsyncClient, db_async_session: AsyncSession, user: User):
    category = ProductCategory(name="Electronics Entertainment 5")
    db_async_session.add(category)
    await db_async_session.commit()

    product = Product(
        name="Laptop Monster W",
        description="Gaming Laptop",
        category_id=category.id,
        price=1200.00,
        stock=10,
        is_active=True
    )
    db_async_session.add(product)
    await db_async_session.commit()

    order = Order(user_id=user.user_id, status=OrderStatus.COMPLETED)
    db_async_session.add(order)
    await db_async_session.commit()

    order_item = OrderItem(
        order_id=order.order_id,
        product_id=product.id,
        quantity=1
    )
    db_async_session.add(order_item)
    await db_async_session.commit()

    response = await client.get("order/sales_report", params={"start_date": "2024-01-01", "min_quantity": 1})
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) > 0
