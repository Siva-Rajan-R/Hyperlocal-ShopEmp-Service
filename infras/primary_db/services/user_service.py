from ..repos.user_repo import UserRepo
from models.service_models.base_service_model import BaseServiceModel
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

class UserService:
    def __init__(self, session: AsyncSession):
        self.session=session
        self.user_repo_obj = UserRepo(session=session)

    async def get_or_create_user(self, name: str, email: str, mobile_number: Optional[str]=None) -> dict:
        user = await self.user_repo_obj.get_by_email(email)
        if user:
            return user
        
        user = await self.user_repo_obj.create(
            name=name,
            email=email,
            mobile_number=mobile_number
        )
        return user

    async def get_by_id(self, user_id: str) -> Optional[dict]:
        return await self.user_repo_obj.get_by_id(user_id)

    async def get_by_email(self, email: str) -> Optional[dict]:
        return await self.user_repo_obj.get_by_email(email)
