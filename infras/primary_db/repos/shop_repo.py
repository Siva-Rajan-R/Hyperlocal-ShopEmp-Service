from ..models.shop_model import Shops
from sqlalchemy import select,update,delete,or_,and_,func,String
from sqlalchemy.dialects.postgresql import insert
from schemas.v1.db_schemas.shop_schemas import CreateShopDbSchema,UpdateShopDbSchema,DeleteShopDbSchema
from schemas.v1.request_schemas.shop_schemas import GetAllShopsSchema,GetShopByIdSchema,GetShopByUserIdSchema,VerifyShoSchema
from models.repo_models.base_repo_model import BaseRepoModel
from hyperlocal_platform.core.decorators.db_session_handler_dec import start_db_transaction
from core.decorators.error_handler_dec import catch_errors
from hyperlocal_platform.core.models.req_res_models import SuccessResponseTypDict,ErrorResponseTypDict,BaseResponseTypDict
from ..models.employee_model import Employees
from fastapi.exceptions import HTTPException
from hyperlocal_platform.core.enums.timezone_enum import TimeZoneEnum
from sqlalchemy.ext.asyncio import AsyncSession
from icecream import ic
from typing import List,Optional

def _map_shop(row) -> Optional[dict]:
    if not row:
        return None
    d = dict(row)
    # Map model to schema fields
    d['category'] = d.pop('categories', '')
    d['datas'] = d.pop('additional_infos', {}) or {}
    d['image_urls'] = []
    return d

class ShopRepo(BaseRepoModel):
    def __init__(self, session:AsyncSession):
        super().__init__(session)
        self.shop_cols=(
            Shops.id,
            Shops.user_id,
            Shops.sequence_id,
            Shops.name,
            Shops.description,
            Shops.tagline,
            Shops.categories,
            Shops.business_infos,
            Shops.address,
            Shops.banner_url,
            Shops.logo_url,
            Shops.additional_infos,
            Shops.updated_at,
            Shops.created_at,
            Shops.ui_id
        )

    async def is_shop_exists(self,user_or_shop_id:str):
        # Checks if shop exists by shop_id or by user_id
        stmt = (
            select(Shops.id)
            .where(
                or_(
                    Shops.id==user_or_shop_id,
                    Shops.user_id==user_or_shop_id
                )
            )
            .limit(1)
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()
    

    @start_db_transaction
    async def create(self, data:CreateShopDbSchema)->dict | None:
        values = data.model_dump(mode="json")

        stmt = (
            insert(Shops)
            .values(**values)
            .returning(*self.shop_cols)
        )

        shop=(await self.session.execute(stmt)).mappings().one_or_none()
        return shop
    

    @start_db_transaction
    async def update(self, data:UpdateShopDbSchema)-> dict | None:
        data_toupdate=data.model_dump(mode="json",exclude=['id','user_id'],exclude_unset=True,exclude_none=True)
        # Map schema to model fields
        if 'category' in data_toupdate:
            data_toupdate['categories'] = data_toupdate.pop('category')
        if 'datas' in data_toupdate:
            data_toupdate['additional_infos'] = data_toupdate.pop('datas')
        if 'image_urls' in data_toupdate:
            data_toupdate.pop('image_urls')

        shop_toupdate=(
            update(Shops)
            .where(
                Shops.id==data.id,
                Shops.user_id==data.user_id
            )
            .values(**data_toupdate)
        ).returning(
            *self.shop_cols
        )

        is_updated=(await self.session.execute(shop_toupdate)).mappings().one_or_none()
        return is_updated
    

    @start_db_transaction
    async def delete(self,data:DeleteShopDbSchema)-> dict | None:
        shop_todel=(
            delete(Shops)
            .where(
                Shops.id==data.shop_id,
                Shops.user_id==data.user_id
            )
        ).returning(
            *self.shop_cols
        )

        is_deleted=(await self.session.execute(shop_todel)).mappings().one_or_none()
        return is_deleted
    

    async def get(self,data:GetAllShopsSchema)-> List[dict] | list:
        search_term=f"%{data.query}%"
        cursor=(data.offset-1)*data.limit
        created_at=func.date(func.timezone(data.timezone.value,Shops.created_at)).label("created_at")

        shop_stmt=(
            select(
                *self.shop_cols,
                created_at,
            )
            .where(
                and_(
                    or_(
                        Shops.id.ilike(search_term),
                        func.cast(created_at,String).ilike(search_term)
                    ),
                    Shops.sequence_id>cursor
                )
                
            )
            .limit(limit=data.limit)
            .offset(offset=cursor)
        )

        shops=(await self.session.execute(shop_stmt)).mappings().all()
        return shops
    

    async def getby_id(self,data:GetShopByIdSchema)-> dict | None:
        created_at=func.date(func.timezone(data.timezone.value,Shops.created_at)).label("created_at")

        shop_stmt=(
            select(
                *self.shop_cols,
                created_at,
            )
            .where(
                Shops.id==data.shop_id
            )
        )

        shop=(await self.session.execute(shop_stmt)).mappings().one_or_none()
        return shop
    
    

    async def getby_userid(self,data:GetShopByUserIdSchema)-> List[dict] | list:
        created_at=func.date(func.timezone(data.timezone.value,Shops.created_at)).label("created_at")
        shop_stmt=(
            select(
                *self.shop_cols,
                created_at
            )
            .where(
                Shops.user_id==data.user_id
            )
        )

        shops=(await self.session.execute(shop_stmt)).mappings().all()
        return shops
    

    async def verify_shop(self,data:VerifyShoSchema)-> dict | None:
        stmt=(
            select(
                Shops.id
            )
            .where(
                Shops.id==data.shop_id
            )
        )

        result=(await self.session.execute(stmt)).scalar_one_or_none()

        if result:
            return {"id":result,'exists':True}
        
        return {"id":'','exists':False}
    
    

    async def search(self,data:GetAllShopsSchema)-> List[dict] | list:
        search_term=f"%{data.query}%"

        shop_stmt=(
            select(
                Shops.id,
                Shops.additional_infos.label("datas")
            )
            .where(
                or_(
                    Shops.id.ilike(search_term)
                )
            )
            .limit(limit=data.limit)
        )

        shop=(await self.session.execute(shop_stmt)).mappings().all()
        return shop
