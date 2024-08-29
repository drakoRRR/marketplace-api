from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.products.models import Product
from src.shopping_cart.models import Cart, CartItem


class CartService:
    def __init__(self, db: AsyncSession, user_id: UUID):
        self.db = db
        self.user_id = user_id

    async def get_or_create_cart(self) -> Cart:
        cart = await self.db.execute(select(Cart).where(Cart.user_id == self.user_id))
        cart = cart.scalars().first()

        if not cart:
            cart = Cart(user_id=self.user_id)
            self.db.add(cart)
            await self.db.commit()
            await self.db.refresh(cart)

        return cart

    async def add_product_to_cart(self, product_id: UUID, quantity: int = 1) -> CartItem:
        cart = await self.get_or_create_cart()

        product = await self.db.execute(select(Product).where(Product.id == product_id))
        product = product.scalars().first()

        if product.stock < quantity:
            raise ValueError("Not enough stock available")

        product.stock -= quantity

        cart_item = await self.db.execute(
            select(CartItem).where(CartItem.cart_id == cart.cart_id, CartItem.product_id == product_id))
        cart_item = cart_item.scalars().first()

        if cart_item:
            cart_item.quantity += quantity
        else:
            cart_item = CartItem(cart_id=cart.cart_id, product_id=product_id, quantity=quantity)
            self.db.add(cart_item)

        await self.db.commit()
        await self.db.refresh(cart_item)
        return cart_item

    async def remove_product_from_cart(self, product_id: UUID) -> None:
        cart = await self.get_or_create_cart()

        cart_item = await self.db.execute(
            select(CartItem).where(CartItem.cart_id == cart.cart_id, CartItem.product_id == product_id))
        cart_item = cart_item.scalars().first()

        if cart_item:
            product = await self.db.execute(select(Product).where(Product.id == product_id))
            product = product.scalars().first()

            product.stock += cart_item.quantity

            await self.db.delete(cart_item)
            await self.db.commit()

    async def update_product_quantity(self, product_id: UUID, quantity: int) -> CartItem:
        cart = await self.get_or_create_cart()

        cart_item = await self.db.execute(
            select(CartItem).where(CartItem.cart_id == cart.cart_id, CartItem.product_id == product_id)
        )
        cart_item = cart_item.scalars().first()

        if cart_item:
            cart_item.quantity = quantity
            await self.db.commit()
            await self.db.refresh(cart_item)
            return cart_item
        else:
            raise ValueError("Product not found in cart")
