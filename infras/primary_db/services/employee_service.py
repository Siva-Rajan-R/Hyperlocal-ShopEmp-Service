from icecream import ic
from ..repos.employee_repo import EmployeeRepo
from sqlalchemy import select,update,delete,or_,and_,func,String
from schemas.v1.db_schemas.employee_schemas import CreateEmployeeDbSchema,UpdateEmployeeDbSchema
from schemas.v1.request_schemas.employee_schemas import CreateEmployeeSchema,UpdateEmployeeSchema,DeleteEmployeeSchema,GetAllEmployeesSchema,GetEmployeeByIdSchema,GetEmployeeByShopIdSchema,VerifyEmployeeSchema
from .shop_service import ShopService
from models.service_models.base_service_model import BaseServiceModel
from core.decorators.error_handler_dec import catch_errors
from fastapi.exceptions import HTTPException
from hyperlocal_platform.core.enums.timezone_enum import TimeZoneEnum
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional,List,Union
from hyperlocal_platform.core.utils.uuid_generator import generate_uuid
from core.data_formats.enums.employee_enums import EmployeeDepartmentEnums,EmployeeRoleEnums
from hyperlocal_platform.core.decorators.db_session_handler_dec import start_db_transaction


class EmployeeService(BaseServiceModel):
    def __init__(self, session:AsyncSession):
        super().__init__(session)
        self.employee_repo_obj=EmployeeRepo(session=session)


    async def create(self, data:CreateEmployeeSchema,user_id:str,account_id:str)-> dict:
        employee_id=generate_uuid()
        data_toadd=CreateEmployeeDbSchema(
            **data.model_dump(),
            id=employee_id,
            added_by=user_id,
            is_accepted=False,
            account_id=account_id
        )
        res=await self.employee_repo_obj.create(data=data_toadd)
        return res


    async def update(self, data:UpdateEmployeeSchema,) -> dict | None:
        data_toupdate=data=data.model_dump(exclude_unset=True,exclude_none=True)
        data=UpdateEmployeeDbSchema(
            **data_toupdate
        )

        res=await self.employee_repo_obj.update(data=data)
        return res

    async def delete(self,data:DeleteEmployeeSchema)-> dict | None:
        res=await self.employee_repo_obj.delete(data=data)
        return res
    

    async def get(self,data:GetAllEmployeesSchema)-> List[dict] | list:
        """This service method for internal use only not to expose it on public !"""
        res=await self.employee_repo_obj.get(data=data)

        return res
        
    

    async def getby_id(self,data:GetEmployeeByIdSchema)-> dict | None:
        """This service method for internal use only not to expose it on public !"""
        res=await self.employee_repo_obj.getby_id(data=data)
        return res

    

    async def getby_shopid(self,data:GetEmployeeByShopIdSchema)-> List[dict] | list:
        """This service method for internal use only not to expose it on public !"""
        res=await self.employee_repo_obj.getby_shopid(data=data)
        return res
    

    async def verify_employee(self,data:VerifyEmployeeSchema)->dict:
        if not data.employee_id and not data.mobile_number and not data.email:
            return {'id':'','exists':False}
        
        res=await self.employee_repo_obj.verify_employee(data=data)

        return res
    
    async def search(self, query:str, limit:int):
        """This is just a wrapper for ABC(Abstract Class) of BaseService"""
        ...


