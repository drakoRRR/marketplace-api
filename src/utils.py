from passlib.hash import bcrypt
from sqlalchemy import select

from src.database import async_session
from src.auth.models import User


async def create_admin_user():
    async with async_session() as db:
        result = await db.execute(
            select(User).filter(User.user_name == "admin")
        )
        admin_user = result.scalars().first()

        if not admin_user:
            hashed_password = bcrypt.hash("admin")

            admin_user = User(
                user_name="admin",
                email="admin@example.com",
                hashed_password=hashed_password,
                is_active=True,
                is_superuser=True
            )

            db.add(admin_user)
            await db.commit()
            await db.refresh(admin_user)
