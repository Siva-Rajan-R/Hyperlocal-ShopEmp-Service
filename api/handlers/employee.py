from infras.primary_db.services.employee_service import EmployeeService,AsyncSession
from schemas.v1.request_schemas.employee_schemas import CreateEmployeeSchema,UpdateEmployeeSchema,GetEmployeeByIdSchema,GetAllEmployeesSchema,GetEmployeeByShopIdSchema,VerifyEmployeeSchema,DeleteEmployeeSchema
from schemas.v1.response_schemas.user_schemas.employee_schemas import EmployeeGetResponseSchema,EmployeeCreateResponseSchema,EmployeeDeleteResponseSchema,EmployeeUpdateResponseSchema
from messaging.saga_producer import SagaProducer,SagaStatusEnum
from core.data_formats.enums.employee_enums import EmployeeRoleEnums
from infras.primary_db.services.shop_service import ShopService
from core.data_formats.enums.saga_enums import SagaTypeEnums
from infras.primary_db.repos.employee_repo import EmployeeRepo
from fastapi.exceptions import HTTPException
from hyperlocal_platform.core.enums.timezone_enum import TimeZoneEnum
from hyperlocal_platform.core.models.req_res_models import SuccessResponseTypDict,BaseResponseTypDict,ErrorResponseTypDict
from hyperlocal_platform.infras.saga.schemas import CreateSagaStateSchema
from hyperlocal_platform.core.utils.uuid_generator import generate_uuid
from hyperlocal_platform.core.enums.saga_state_enum import SagaStepsValueEnum
from hyperlocal_platform.core.typed_dicts.saga_status_typ_dict import SagaStateExecutionTypDict
from hyperlocal_platform.core.utils.routingkey_builder import generate_routingkey,RoutingkeyActions,RoutingkeyState,RoutingkeyVersions
from hyperlocal_platform.core.enums.routingkey_enum import RoutingkeyState,RoutingkeyActions
from infras.read_db.services.employee_service import ReadDbEmployeeService
from typing import Optional
from infras.read_db.main import MONGO_CLIENT,EMPLOYEES_COLLECTION
from core.constants import EMP_SERVICE_NAME,SHOP_SERVICE_NAME
from icecream import ic
from core.utils.validate_fields import validate_fields,validate_internal_fields

class HandleEmployeeRequest:
    def __init__(self,session:AsyncSession):
        self.session=session

    async def create(self,data:CreateEmployeeSchema,account_id:str):
        # for checking the accounts
        is_emp_exists=await EmployeeService(session=self.session).verify_employee(data=VerifyEmployeeSchema(shop_id=data.shop_id,email=data.email))
        if is_emp_exists['exists']:
            raise HTTPException(
                status_code=409,
                detail=ErrorResponseTypDict(
                    msg="Error : Creating Employee",
                    description="Employee already exists",
                    success=False,
                    status_code=409
                )
            )
        
        saga_id:str=generate_uuid()
        payload={'employees':{**data.model_dump(mode="json"),"account_id":account_id}}
        r_key="accounts.service.routing.key"
        r_exchange="accounts.service.exchange"
        reply_key="employees.producer.routing.key"
        reply_exchange="employees.producer.exchange"
        reply_service_name="EMPLOYEES"
        reply_entity_name="create_employee"

        
        return await SagaProducer.emit(
            session=self.session,
            routing_key=r_key,
            exchange_name=r_exchange,
            headers={
                "reply_key":reply_key,
                "reply_exchange":reply_exchange,
                "reply_service_name":reply_service_name,
                "reply_entity_name":reply_entity_name,
                "service_name":"ACCOUNTS",
                "entity_name":"verify_account",
                "body":{'email':data.email}

            },
            saga_payload=CreateSagaStateSchema(
                id=saga_id,
                status=SagaStatusEnum.IN_PROGRESS,
                type=SagaTypeEnums.EMPLOYEE_CREATED,
                data=payload,
                steps={
                    "ACCOUNT_VERIFICATION":SagaStepsValueEnum.PENDING.value,
                    "ACCOUNT_CREATION":SagaStepsValueEnum.PENDING.value
                },
                execution=SagaStateExecutionTypDict(
                    step="ACCOUNT_VERIFICATION",
                    service="ACCOUNTS"
                ),
                error=None
            ),
        )


    async def update(self,data:UpdateEmployeeSchema):
        res=await EmployeeService(session=self.session).update(data=data)
        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                msg="Employee Updated Successfully",
                status_code=200,
                success=True
            ),
            data=EmployeeUpdateResponseSchema(**res) if res else None
        )
    

    async def delete(self,data:DeleteEmployeeSchema):
        res=await EmployeeService(session=self.session).delete(data=data)
        ic(res)
        if res:
            return SuccessResponseTypDict(
                detail=BaseResponseTypDict(
                    msg="Employee Deleted Successfully",
                    success=True,
                    status_code=200
                ),
                data=EmployeeDeleteResponseSchema(**res) if res else None
            )
        
        raise HTTPException(
            status_code=404,
            detail=ErrorResponseTypDict(
                msg="Error : Deleting employee",
                description="Invalid Employee data (id,shop_id)",
                success=False,
                status_code=404
            )
        )
    
    async def get_all(self,data:GetAllEmployeesSchema):
        res=await EmployeeService(session=self.session).get(data=data)
        ic(res)
        
        if data.offset in (0, 1):
            data_to_send = {
                "overall_datas": res.get("overall_datas", {}),
                "datas": [EmployeeGetResponseSchema(**r) for r in res.get("datas", [])]
            }
        else:
            data_to_send = [EmployeeGetResponseSchema(**r) for r in res.get("datas", [])]

        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                msg="Employees fetched successfully",
                status_code=200,
                success=True
            ),

            data=data_to_send
        )
    
    async def getby_id(self,data:GetEmployeeByIdSchema):
        res=await EmployeeService(session=self.session).getby_id(data=data)

        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                msg="Employee fetched successfully",
                status_code=200,
                success=True
            ),
            data=EmployeeGetResponseSchema(**res) if res else None
        )
    
    async def getby_shopid(self,data:GetEmployeeByShopIdSchema):
        res=await EmployeeService(session=self.session).getby_shopid(data=data)
        
        if data.offset in (0, 1):
            data_to_send = {
                "overall_datas": res.get("overall_datas", {}),
                "datas": [EmployeeGetResponseSchema(**r) for r in res.get("datas", [])]
            }
        else:
            data_to_send = [EmployeeGetResponseSchema(**r) for r in res.get("datas", [])]

        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                msg="Employee fetched successfully",
                status_code=200,
                success=True
            ),
            data=data_to_send
        )

    async def search(self,q:str,limit:int,read_db:Optional[bool]=True):
        res=await ReadDbEmployeeService(payload={},conditions={}).get(query=q,limit=limit)
        if not read_db:
            res=await EmployeeService(session=self.session).search(query=q,limit=limit)

        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                msg="Employee fetched successfully",
                status_code=200,
                success=True
            ),
            data=res
        )