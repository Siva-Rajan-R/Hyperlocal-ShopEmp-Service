from ..models.user_model import Users
from sqlalchemy import select, insert, update
from models.repo_models.base_repo_model import BaseRepoModel
from hyperlocal_platform.core.decorators.db_session_handler_dec import start_db_transaction
from sqlalchemy.ext.asyncio import AsyncSession
from hyperlocal_platform.core.utils.uuid_generator import generate_uuid
from typing import Optional

class UserRepo:
    def __init__(self, session: AsyncSession):
        self.session=session
        self.user_cols = (
            Users.id,
            Users.sequence_id,
            Users.name,
            Users.mobile_number,
            Users.email,
            Users.additional_infos,
            Users.created_at,
            Users.updated_at
        )

    async def get_by_email(self, email: str) -> Optional[dict]:
        stmt = select(*self.user_cols).where(Users.email == email)
        res = (await self.session.execute(stmt)).mappings().one_or_none()
        return dict(res) if res else None

    async def get_by_id(self, user_id: str) -> Optional[dict]:
        stmt = select(*self.user_cols).where(Users.id == user_id)
        res = (await self.session.execute(stmt)).mappings().one_or_none()
        return dict(res) if res else None

    @start_db_transaction
    async def create(self, name: str, email: str, mobile_number: Optional[str]=None, additional_infos: Optional[dict] = None) -> dict:
        user_id = generate_uuid()
        stmt = (
            insert(Users)
            .values(
                id=user_id,
                name=name,
                email=email,
                mobile_number=mobile_number,
                additional_infos=additional_infos or {}
            )
            .returning(*self.user_cols)
        )
        res = (await self.session.execute(stmt)).mappings().one()
        return dict(res)
