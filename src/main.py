import uvicorn

from dotenv import load_dotenv
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi_pagination import add_pagination

from sqladmin import Admin

from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

from src.admin.auth import authentication_backend
from src.admin.models import UserAdmin, ProductAdmin, ProductCategoryAdmin
from src.config import DEBUG
from src.auth.routers import auth_router
from src.database import async_engine
from src.products.models import Product
from src.products.routers import product_router
from src.utils import create_admin_user
from src.database import redis_conn
from src.shopping_cart.routers import cart_router
from src.orders.routers import order_router


load_dotenv()


def create_app():
    fast_api_app = FastAPI(
        debug=bool(DEBUG),
        docs_url="/api/docs/",
    )

    fast_api_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    add_pagination(fast_api_app)
    FastAPICache.init(RedisBackend(redis_conn), prefix="fastapi-cache")

    return fast_api_app


fastapi_app = create_app()


@fastapi_app.on_event("startup")
async def startup():
    await create_admin_user()


admin = Admin(fastapi_app, async_engine, authentication_backend=authentication_backend)

admin.add_view(UserAdmin)
admin.add_view(ProductAdmin)
admin.add_view(ProductCategoryAdmin)


main_api_router = APIRouter()
fastapi_app.include_router(auth_router, prefix="/auth", tags=["Auth"])
fastapi_app.include_router(product_router, prefix="/products", tags=["Products"])
fastapi_app.include_router(cart_router, prefix="/cart", tags=["Shopping Cart"])
fastapi_app.include_router(order_router, prefix="/order", tags=["Orders"])
fastapi_app.include_router(main_api_router)


if __name__ == "__main__":
    uvicorn.run(fastapi_app, host="0.0.0.0", port=5000)
