from ..repos.shop_repo import ShopRepo
from sqlalchemy import select,update,delete,or_,and_,func,String
from .employee_service import EmployeeRepo
from schemas.v1.db_schemas.shop_schema import CreateShopDbSchema,UpdateShopDbSchema
from schemas.v1.request_schemas.shop_schema import CreateShopSchema,UpdateShopSchema
from models.service_models.base_service_model import BaseServiceModel
from core.decorators.error_handler_dec import catch_errors
from ..models.employee_model import Employees
from fastapi.exceptions import HTTPException
from hyperlocal_platform.core.enums.timezone_enum import TimeZoneEnum
from sqlalchemy.ext.asyncio import AsyncSession
from hyperlocal_platform.core.utils.uuid_generator import generate_uuid
from typing import Optional
from schemas.v1.response_schemas.shop_schema import ResponseShopSchema
from hyperlocal_platform.core.decorators.db_session_handler_dec import start_db_transaction

class ShopService(BaseServiceModel):
    def __init__(self, session:AsyncSession):
        super().__init__(session)
        self.shop_repo_obj=ShopRepo(session=session)


    @catch_errors
    async def create(self, data:CreateShopSchema,account_id:str):
        shop_id:str=generate_uuid()
        data=CreateShopDbSchema(
            **data.model_dump(),
            id=shop_id,
            account_id=account_id
        )
        
        if (await EmployeeRepo(session=self.session).is_employee_exists(employee_account_id=account_id)):
            return False
        
        await self.session.close()

        res=await self.shop_repo_obj.create(data=data)
        return res
        
    
    @catch_errors
    async def update(self, data:UpdateShopSchema,account_id:str):
        res=await self.shop_repo_obj.update(data=UpdateShopDbSchema(**data.model_dump(exclude_unset=True,exclude_none=True),is_verified=False,account_id=account_id))
        return res
    
    @catch_errors
    async def delete(self,shop_id:str,account_id:str):
        res=await self.shop_repo_obj.delete(shop_id=shop_id,account_id=account_id)
        return res
    

    @catch_errors
    async def get(self,timezone:TimeZoneEnum,query:Optional[str]='',limit:Optional[int]=10,offset:Optional[int]=0):
        """This repo method for internal use only not to expose it on public !"""
        res=await self.shop_repo_obj.get(query=query,limit=limit,offset=offset,timezone=timezone)

        return res
    

    @catch_errors
    async def getby_id(self,shop_id:str,timezone:TimeZoneEnum):
        res=await self.shop_repo_obj.getby_id(shop_id=shop_id,timezone=timezone)
        # if res:
        #     res=ResponseShopSchema(**res)
        return res
    
    @catch_errors
    async def getby_shop_acc_id(self,shop_id:str,account_id:str,timezone:TimeZoneEnum):
        res=await self.shop_repo_obj.getby_shop_acc_id(shop_id=shop_id,account_id=account_id,timezone=timezone)

        return res
    

    @catch_errors
    async def getby_accountid(self,account_id:str,timezone:TimeZoneEnum):
        res=await self.shop_repo_obj.getby_accountid(account_id=account_id,timezone=timezone)

        return res
    

    @catch_errors
    async def search(self, query:str, limit:int):
        res=await self.shop_repo_obj.search(query=query,limit=limit)

        return res

