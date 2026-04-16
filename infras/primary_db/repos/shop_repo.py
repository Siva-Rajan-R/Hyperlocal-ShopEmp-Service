from ..models.shop_model import Shops
from sqlalchemy import select,update,delete,or_,and_,func,String
from schemas.v1.db_schemas.shop_schema import CreateShopDbSchema,UpdateShopDbSchema
from models.repo_models.base_repo_model import BaseRepoModel
from hyperlocal_platform.core.decorators.db_session_handler_dec import start_db_transaction
from core.decorators.error_handler_dec import catch_errors
from hyperlocal_platform.core.models.req_res_models import SuccessResponseTypDict,ErrorResponseTypDict,BaseResponseTypDict
from ..models.employee_model import Employees
from fastapi.exceptions import HTTPException
from hyperlocal_platform.core.enums.timezone_enum import TimeZoneEnum
from sqlalchemy.ext.asyncio import AsyncSession
from icecream import ic



class ShopRepo(BaseRepoModel):
    def __init__(self, session:AsyncSession):
        super().__init__(session)
        self.shop_cols=(
            Shops.id,
            Shops.account_id,
            Shops.datas
        )


    @catch_errors
    async def is_shop_exists(self,account_shop_employee_id:str):
        return (await self.session.execute(
            select(Shops.id)
            .where(
                or_(
                    Shops.id==account_shop_employee_id,
                    Shops.account_id==account_shop_employee_id,
                    Employees.id==account_shop_employee_id,
                    Employees.account_id==account_shop_employee_id
                )
            )
            .limit(1)
            .join(Employees,Employees.shop_id==Shops.id)
        )).scalar_one_or_none()
    

    @catch_errors
    @start_db_transaction
    async def create(self, data:CreateShopDbSchema):
        self.session.add(Shops(**data.model_dump(mode="json")))
        return True
    
    @catch_errors
    @start_db_transaction
    async def update(self, data:UpdateShopDbSchema):
        ic(data.model_dump(mode="json",exclude=['id','account_id'],exclude_unset=True,exclude_none=True))
        employee_shop_id = (
            select(Employees.shop_id)
            .where(
                Employees.shop_id==data.id,
                Employees.account_id == data.account_id
            )
        )
        shop_toupdate=(
            update(Shops)
            .where(
                or_(
                    and_(
                        Shops.id==data.id,
                        Shops.account_id==data.account_id
                    ),
                    Shops.id.in_(employee_shop_id)
                )
            )
            .values(**data.model_dump(mode="json",exclude=['id','account_id'],exclude_unset=True,exclude_none=True))
        ).returning(Shops.id)

        is_updated=(await self.session.execute(shop_toupdate)).scalar_one_or_none()
        
        await self.session.commit()
        return is_updated
    
    @catch_errors
    @start_db_transaction
    async def delete(self,shop_id:str,account_id:str):
        shop_todel=(
            delete(Shops)
            .where(
                Shops.id==shop_id,
                Shops.account_id==account_id
            )
        ).returning(Shops.id)

        is_deleted=(await self.session.execute(shop_todel)).scalar_one_or_none()

        return is_deleted
    

    @catch_errors
    async def get(self,query:str,limit:int,offset:int,timezone:TimeZoneEnum):
        """This repo method for internal use only not to expose it on public !"""
        search_term=f"%{query}%"
        cursor=(offset-1)*limit
        created_at=func.date(func.timezone(timezone.value,Shops.created_at)).label("created_at")
        print(query,limit,offset,timezone,created_at)

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
            .limit(limit=limit)
            .order_by(created_at) 
        )

        shops=(await self.session.execute(shop_stmt)).mappings().all()

        return shops
    

    @catch_errors
    async def getby_id(self,shop_id:str,timezone:TimeZoneEnum):
        created_at=func.date(func.timezone(timezone.value,Shops.created_at)).label("created_at")

        shop_stmt=(
            select(
                *self.shop_cols,
                created_at,
            )
            .where(
                Shops.id==shop_id
            )
        )

        shop=(await self.session.execute(shop_stmt)).mappings().one_or_none()

        return shop
    

    @catch_errors
    async def  getby_shop_acc_id(self,shop_id:str,account_id:str,timezone:TimeZoneEnum):
        created_at=func.date(func.timezone(timezone.value,Shops.created_at)).label("created_at")

        shop_stmt=(
            select(
                *self.shop_cols,
                created_at,
            )
            .where(
                Shops.id==shop_id,
                Shops.account_id==account_id
            )
        )

        shop=(await self.session.execute(shop_stmt)).mappings().one_or_none()

        return shop
    

    @catch_errors
    async def getby_accountid(self,account_id:str,timezone:TimeZoneEnum):
        created_at=func.date(func.timezone(timezone.value,Shops.created_at)).label("created_at")
        shop_stmt=(
            select(
                *self.shop_cols,
                created_at

            )
            .where(
                Shops.account_id==account_id
            )
        )

        shops=(await self.session.execute(shop_stmt)).mappings().all()

        return shops
    

    @catch_errors
    async def search(self, query:str, limit:int):
        search_term=f"%{query}%"

        shop_stmt=(
            select(
                Shops.id,
                Shops.datas
            )
            .where(
                or_(
                    Shops.id.ilike(search_term)
                )
            )
            .limit(limit=limit)
        )

        shop=(await self.session.execute(shop_stmt)).mappings().all()

        return shop

