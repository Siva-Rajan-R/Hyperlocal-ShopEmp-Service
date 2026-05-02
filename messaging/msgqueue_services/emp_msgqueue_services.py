from infras.primary_db.services.employee_service import EmployeeService
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.v1.response_schemas.msgqueue_schemas.employee_schemas import EmployeeCreateResponseSchema,EmployeeUpdateResponseSchema,EmployeeDeleteResponseSchema,EmployeeGetResponseSchema
from schemas.v1.request_schemas.employee_schemas import CreateEmployeeSchema,UpdateEmployeeSchema,DeleteEmployeeSchema,GetAllEmployeesSchema,GetEmployeeByIdSchema,GetEmployeeByShopIdSchema,VerifyEmployeeSchema
from typing import Union,List,Optional
from infras.primary_db.main import AsyncShopEmployeeLocalSession

class MessagingQueueEmployeeService:
    
    async def verify_employee(self,data:Union[VerifyEmployeeSchema,dict]):
        if isinstance(data, dict):
            data = VerifyEmployeeSchema(**data)
        async with AsyncShopEmployeeLocalSession() as session:
            emp_service_obj=EmployeeService(session=session)
            res=await emp_service_obj.verify_employee(data=data)

            return res
        

    async def get_employees(self,data:Union[GetAllEmployeesSchema,dict]):
        if isinstance(data, dict):
            data = GetAllEmployeesSchema(**data)
        async with AsyncShopEmployeeLocalSession() as session:
            emp_service_obj=EmployeeService(session=session)
            res=await emp_service_obj.get(data=data)

            if not res:
                return res

            return [EmployeeGetResponseSchema(**r).model_dump(mode="json") for r in res]
    
    async def get_employee_by_id(self,data:Union[GetEmployeeByIdSchema,dict]):
        if isinstance(data, dict):
            data = GetEmployeeByIdSchema(**data)
        async with AsyncShopEmployeeLocalSession() as session:
            emp_service_obj=EmployeeService(session=session)
            res=await emp_service_obj.getby_id(data=data)

            if not res:
                return res
            
            return EmployeeGetResponseSchema(**res).model_dump(mode="json")
    
    async def get_employee_by_shop_id(self,data:Union[GetEmployeeByShopIdSchema,dict]):
        if isinstance(data, dict):
            data = GetEmployeeByShopIdSchema(**data)
        async with AsyncShopEmployeeLocalSession() as session:
            emp_service_obj=EmployeeService(session=session)
            res=await emp_service_obj.getby_shopid(data=data)

            if not res:
                return res
            
            return [EmployeeGetResponseSchema(**r).model_dump(mode="json") for r in res]


    