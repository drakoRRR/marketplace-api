from sqladmin import ModelView, action
from starlette.responses import RedirectResponse
from fastapi import Request

from src.auth.models import User
from src.auth.dals import UserDAL
from src.auth.hashing import Hasher
from src.database import async_session
from src.exceptions import UserAlreadyExistsException
from src.orders.models import Order
from src.products.models import Product, ProductCategory


async def get_current_user(request: Request):
    async with async_session() as session:
        token = request.session.get("token")
        if not token:
            return None
        return await session.get(User, token)


class BaseModel(ModelView):
    page_size = 50
    page_size_options = [25, 50, 100, 200]

    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True
    can_export = True


class UserAdmin(BaseModel, model=User):
    name = "User"
    name_plural = "Users"
    icon = "fa-solid fa-user"

    column_list = [User.user_id, User.user_name, User.email, User.created_at]
    column_searchable_list = [User.user_name, User.email]
    form_columns = [User.user_name, User.email, User.hashed_password]

    async def on_model_change(self, data, model, is_created, request):
        if "hashed_password" in data:
            data["hashed_password"] = Hasher.get_password_hash(data["hashed_password"])
            model.hashed_password = data["hashed_password"]

        async with async_session() as session:
            user_dal = UserDAL(session)
            try:
                user = await user_dal.create_user(
                    user_name=data["user_name"],
                    email=data["email"],
                    hashed_password=data["hashed_password"],
                )
            except UserAlreadyExistsException:
                return super(UserAdmin, self).on_model_change(data, model, is_created, request)
            model.user_id = user.user_id
            model.user_name = user.user_name
            model.email = user.email
            model.hashed_password = user.hashed_password

        return super(UserAdmin, self).on_model_change(data, model, is_created, request)

    @action(
        name="give_admin_status",
        label="Give Admin Status",
        confirmation_message="Are you sure you want to approve admin status to the selected users?",
        add_in_detail=True,
        add_in_list=True,
    )
    async def approve_users(self, request: Request):
        current_user = await get_current_user(request)
        if not current_user or not current_user.is_superuser:
            referer = request.headers.get("Referer")
            if referer:
                return RedirectResponse(referer)
            else:
                return RedirectResponse(request.url_for("admin:list", identity=self.identity))

        pks = request.query_params.get("pks", "").split(",")
        if pks:
            async with async_session() as session:
                async with session.begin():
                    for pk in pks:
                        user = await session.get(User, pk)
                        if user:
                            user.is_superuser = True
                            session.add(user)

        referer = request.headers.get("Referer")
        if referer:
            return RedirectResponse(referer)
        else:
            return RedirectResponse(request.url_for("admin:list", identity=self.identity))


class ProductAdmin(BaseModel, model=Product):
    name = "Product"
    name_plural = "Products"
    icon = "fa-solid"

    column_list = [Product.name, Product.is_active, Product.price, Product.category_id]
    column_searchable_list = [Product.name]
    form_columns = [Product.name, Product.is_active, Product.price, Product.category_id, Product.description,
                    Product.discounts]


class ProductCategoryAdmin(BaseModel, model=ProductCategory):
    name = "Product Category"
    name_plural = "Product Categories"
    icon = "fa-solid"

    column_list = [ProductCategory.id, ProductCategory.name, ProductCategory.name]
    column_searchable_list = [ProductCategory.name]
    form_columns = [ProductCategory.name, ProductCategory.description, ProductCategory.parent]


class OrdersAdmin(BaseModel, model=Order):
    name = "Orders"
    name_plural = "Orders"
    icon = "fa-solid"

    column_list = [Order.order_id, Order.user_id, Order.status]
    column_searchable_list = [Order.order_id]
    form_columns = [Order.user, Order.items, Order.status]
