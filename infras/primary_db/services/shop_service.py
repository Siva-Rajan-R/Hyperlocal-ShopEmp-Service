from ..repos.shop_repo import ShopRepo
from sqlalchemy import select,update,delete,or_,and_,func,String
from .employee_service import EmployeeService
from schemas.v1.db_schemas.shop_schemas import CreateShopDbSchema,UpdateShopDbSchema,DeleteShopDbSchema
from schemas.v1.request_schemas.shop_schemas import CreateShopSchema,UpdateShopSchema,GetAllShopsSchema,GetShopByIdSchema,DeleteShopSchema,GetShopByUserIdSchema,VerifyShoSchema
from models.service_models.base_service_model import BaseServiceModel
from core.decorators.error_handler_dec import catch_errors
from ..models.employee_model import Employees
from fastapi.exceptions import HTTPException
from hyperlocal_platform.core.enums.timezone_enum import TimeZoneEnum
from sqlalchemy.ext.asyncio import AsyncSession
from hyperlocal_platform.core.utils.uuid_generator import generate_uuid
from typing import Optional,List
from hyperlocal_platform.core.decorators.db_session_handler_dec import start_db_transaction
from icecream import ic

class ShopService(BaseServiceModel):
    def __init__(self, session:AsyncSession):
        super().__init__(session)
        self.shop_repo_obj=ShopRepo(session=session)


    async def create(self, data:CreateShopSchema, user_id:str)-> dict | None:
        shop_id:str=generate_uuid()
        data_toadd=CreateShopDbSchema(
            **data.model_dump(mode="json"),
            id=shop_id,
            user_id=user_id
        )

        res=await self.shop_repo_obj.create(data=data_toadd)
        return res
        
    
    async def update(self, data:UpdateShopSchema, user_id:str)-> dict | None:
        ic("Update service started")
        data_toupdate=UpdateShopDbSchema(**data.model_dump(mode="json",exclude_unset=True,exclude_none=True), user_id=user_id)
        ic(data_toupdate)
        res=await self.shop_repo_obj.update(data=data_toupdate)
        return res
    
    async def delete(self,data:DeleteShopSchema, user_id:str)-> dict | None:
        data_todel=DeleteShopDbSchema(
            **data.model_dump(mode="json"),
            user_id=user_id
        )
        res=await self.shop_repo_obj.delete(data=data_todel)
        return res
    

    async def get(self,data:GetAllShopsSchema)-> List[dict] | list:
        res=await self.shop_repo_obj.get(data=data)
        return res
    

    async def getby_id(self,data:GetShopByIdSchema)-> dict | None:
        res=await self.shop_repo_obj.getby_id(data=data)
        return res
    
    
    async def getby_userid(self,data:GetShopByUserIdSchema)-> List[dict] | list:
        res=await self.shop_repo_obj.getby_userid(data=data)
        return res
    
    async def verify_shop(self,data:VerifyShoSchema)-> bool:
        res=await self.shop_repo_obj.verify_shop(data=data)
        return res
    

    async def search(self, data:GetAllShopsSchema):
        res=await self.shop_repo_obj.search(data=data)
        return res
