from infras.primary_db.repos.shop_repo import ShopRepo
from sqlalchemy import select,update,delete,or_,and_,func,String
from infras.primary_db.services.shop_service import ShopService
from schemas.v1.db_schemas.shop_schemas import CreateShopDbSchema,UpdateShopDbSchema
from schemas.v1.request_schemas.shop_schemas import CreateShopSchema,UpdateShopSchema,DeleteShopSchema,GetAllShopsSchema,GetShopByUserIdSchema,GetShopByIdSchema
from schemas.v1.response_schemas.user_schemas.shop_schemas import ShopCreateResponseSchema,ShopUpdateResponseSchema,ShopDeleteResponseSchema,ShopGetResponseSchema
from models.service_models.base_service_model import BaseServiceModel
from hyperlocal_platform.core.decorators.db_session_handler_dec import start_db_transaction
from core.decorators.error_handler_dec import catch_errors
from hyperlocal_platform.core.models.req_res_models import SuccessResponseTypDict,ErrorResponseTypDict,BaseResponseTypDict
from infras.primary_db.models.employee_model import Employees
from fastapi.exceptions import HTTPException
from hyperlocal_platform.core.enums.timezone_enum import TimeZoneEnum
from sqlalchemy.ext.asyncio import AsyncSession
from hyperlocal_platform.core.utils.uuid_generator import generate_uuid
from typing import Optional
from icecream import ic

class HandleShopRequest:
    def __init__(self, session:AsyncSession):
        self.session=session


    async def create(self, data:CreateShopSchema, user_id:str):
        ic("User_Id => ",user_id)
        res=await ShopService(session=self.session).create(data=data,user_id=user_id)
        if res:
            return SuccessResponseTypDict(
                detail=BaseResponseTypDict(
                    msg="Shop created successfully",
                    status_code=201,
                    success=True
                ),
                data=res
            )
        
    

    async def update(self, data:UpdateShopSchema, user_id:str):
        res=await ShopService(session=self.session).update(data=data,user_id=user_id)
        if res:
            return SuccessResponseTypDict(
                detail=BaseResponseTypDict(
                    msg="Shop updated successfully",
                    success=True,
                    status_code=200
                ),
                data=res
            )
        
        raise HTTPException(
            status_code=404,
            detail=ErrorResponseTypDict(
                msg="Error : Updating Shop",
                description="Invalid Shop Data (id)",
                success=False,
                status_code=404
            )
        )
    

    async def delete(self,data:DeleteShopSchema, user_id:str):
        res=await ShopService(session=self.session).delete(data=data,user_id=user_id)
        if res:
            return SuccessResponseTypDict(
                detail=BaseResponseTypDict(
                    msg="Shop deleted successfully",
                    success=True,
                    status_code=200
                ),
                data=res
            )
        
        raise HTTPException(
            status_code=404,
            detail=ErrorResponseTypDict(
                msg="Error : Deleting shop",
                description="Invalid Shop Data (id,owner)",
                success=False,
                status_code=404
            )
        )
    


    async def get(self,data:GetAllShopsSchema):
        """This repo method for internal use only not to expose it on public !"""
        res=await ShopService(session=self.session).get(data=data)

        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                msg="Shops fetched successfully",
                success=True,
                status_code=200
            ),
            data=res
        )
    


    async def getby_id(self,data:GetShopByIdSchema):
        res=await ShopService(session=self.session).getby_id(data=data)

        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                msg="Shop fetched successfully",
                success=True,
                status_code=200
            ),
            data=res
        )
    


    async def getby_userid(self,data:GetShopByUserIdSchema):
        res=await ShopService(session=self.session).getby_userid(data=data)

        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                msg="Shops fetched successfully",
                success=True,
                status_code=200
            ),
            data=res
        )
