from sqladmin.authentication import AuthenticationBackend

from fastapi import Request

from src.auth.services import authenticate_user
from src.auth.dals import UserDAL
from src.database import async_session
from src.config import SECRET_KEY


class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        username, password = str(form["username"]), str(form["password"])
        async with async_session() as session:
            user = await authenticate_user(session, username, password)

            if not user.is_superuser:
                return False

            request.session.update({"token": str(user.user_id)})

            return True

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        token = request.session.get("token")

        if not token:
            return False

        async with async_session() as session:
            user_dal = UserDAL(session)
            user = await user_dal.get_user_by_id(token)

            if not user or not user.is_superuser:
                return False

            return True


authentication_backend = AdminAuth(secret_key=SECRET_KEY)
