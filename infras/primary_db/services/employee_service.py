from ..repos.employee_repo import EmployeeRepo
from sqlalchemy import select,update,delete,or_,and_,func,String
from schemas.v1.db_schemas.employee_schema import CreateEmployeeDbSchema,UpdateEmployeeDbSchema
from schemas.v1.request_schemas.employee_schema import CreateEmployeeSchema,UpdateEmployeeSchema
from .shop_service import ShopService
from models.service_models.base_service_model import BaseServiceModel
from core.decorators.error_handler_dec import catch_errors
from fastapi.exceptions import HTTPException
from hyperlocal_platform.core.enums.timezone_enum import TimeZoneEnum
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from hyperlocal_platform.core.utils.uuid_generator import generate_uuid
from core.data_formats.enums.role_enums import RoleEnum
from hyperlocal_platform.core.decorators.db_session_handler_dec import start_db_transaction


class EmployeeService(BaseServiceModel):
    def __init__(self, session:AsyncSession):
        super().__init__(session)
        self.employee_repo_obj=EmployeeRepo(session=session)


    async def create(self, data:CreateEmployeeSchema,account_id:str,account_info:dict):
        account_info=account_info
        if not account_info['is_new']:
            is_owner=await ShopService(session=self.session).getby_accountid(account_id=account_info['id'],timezone=TimeZoneEnum.Asia_Kolkata)
            if len(is_owner)>0:
                return False
            
            is_emp_exists=await self.employee_repo_obj.is_employee_exists(employee_account_id=account_info['id'],shop_id=data.shop_id)
            if is_emp_exists:
                return False
        

        data.datas['name']=None
        data.datas['mobile_number']=None
        employee_id:str=generate_uuid()
        data=CreateEmployeeDbSchema(
            **data.model_dump(),
            id=employee_id,
            added_by=account_id,
            is_accepted=False,
            account_id=account_info['id']
        )
        res=await self.employee_repo_obj.create(data=data)
        return res


    async def update(self, data:UpdateEmployeeSchema,account_info:dict):

        if not account_info:
            return False
        
        acc_name:str=account_info.get('name')
        acc_mobile_number:str=account_info.get('mobile_number')

        emp_name:str=data.datas['name']
        emp_mobile_number:str=data.datas['mobile_number']


        if (acc_name and emp_name) and acc_name.lower()==emp_name.lower():
            data.datas['name']=None
        if (acc_mobile_number and emp_mobile_number)and acc_mobile_number==emp_mobile_number:
            data.datas['mobile_number']=None

        data=UpdateEmployeeDbSchema(
            **data.model_dump(mode="json",exclude_unset=True)
        )

        res=await self.employee_repo_obj.update(data=data)

        return res

    async def delete(self,employee_id:str,shop_id:str,account_id:str):
        res=await self.employee_repo_obj.delete(employee_id=employee_id,shop_id=shop_id,added_acc_id=account_id)
        return res
    

    async def get(self,offset:int,query:Optional[str]="",limit:Optional[int]=10,timezone:Optional[TimeZoneEnum]=TimeZoneEnum.Asia_Kolkata):
        """This service method for internal use only not to expose it on public !"""
        res=await self.employee_repo_obj.get(
            query=query,
            limit=limit,
            offset=offset,
            timezone=timezone
        )

        return res
        
    

    async def getby_id(self,employee_id:str,timezone:Optional[TimeZoneEnum]=TimeZoneEnum.Asia_Kolkata):
        """This service method for internal use only not to expose it on public !"""
        res=await self.employee_repo_obj.getby_id(employee_id=employee_id,timezone=timezone)
        return res

    

    async def getby_shopid(self,shop_id:str,timezone:TimeZoneEnum):
        """This service method for internal use only not to expose it on public !"""
        res=await self.employee_repo_obj.getby_shopid(shop_id=shop_id,timezone=timezone)
        return res
    
    async def search(self, query:str, limit:int):
        """This is just a wrapper for ABC(Abstract Class) of BaseService"""
        ...


