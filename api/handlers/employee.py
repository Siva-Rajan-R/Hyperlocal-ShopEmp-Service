from infras.primary_db.services.employee_service import EmployeeService,AsyncSession
from schemas.v1.request_schemas.employee_schema import CreateEmployeeSchema,UpdateEmployeeSchema,CREATE_EMPLOYEE_MANDATORY_FIELDS,UPDATE_EMPLOYEE_MANDATORY_FIELDS
from messaging.saga_producer import SagaProducer,SagaStatusEnum
from core.data_formats.enums.role_enums import RoleEnum
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
        # await validate_fields(service_name="EMPLOYEE",shop_id=data.shop_id,incoming_fields=data.datas)4
        await validate_internal_fields(fields_tocheck=CREATE_EMPLOYEE_MANDATORY_FIELDS,incoming_fields=data.datas)
        shop_id=data.datas.get("shop_id")
        ic(data.datas)
        if not (await ShopService(session=self.session).getby_id(shop_id=shop_id,timezone=TimeZoneEnum.Asia_Kolkata)):
            raise HTTPException(
                status_code=404,
                detail=ErrorResponseTypDict(
                    msg="Error : Creating employee",
                    description="Invalid shop id",
                    status_code=404,
                    success=False
                )
            )
        
        data=data.datas
        data['account_id']=account_id
        data['source']='marketplace'

        ic(data)

        # for checking the accounts
        saga_id:str=generate_uuid()
        payload={'employees':data}
        r_key=generate_routingkey(domain=EMP_SERVICE_NAME,work_for=EMP_SERVICE_NAME,action=RoutingkeyActions.CREATE,state=RoutingkeyState.REQUESTED,version=RoutingkeyVersions.V1)
        return await SagaProducer.emit(
            session=self.session,
            routing_key=r_key,
            exchange_name="employees.employees.accounts.exchange",
            saga_payload=CreateSagaStateSchema(
                id=saga_id,
                status=SagaStatusEnum.IN_PROGRESS,
                type=SagaTypeEnums.EMPLOYEE_CREATED,
                data=payload,
                steps={
                    f"accounts.{RoutingkeyActions.CREATE.value.lower()}":SagaStepsValueEnum.PENDING.value
                },
                execution=SagaStateExecutionTypDict(
                    step="employees:create:requested",
                    service=f"{EMP_SERVICE_NAME.upper()}-SERVICE"
                ),
                error=None
            ),
        )


    async def update(self,data:UpdateEmployeeSchema,account_id:str):
        # need to do a pre operation steps
        # await validate_fields(service_name="EMPLOYEE",shop_id=data.shop_id,incoming_fields=data.datas)
        await validate_internal_fields(fields_tocheck=UPDATE_EMPLOYEE_MANDATORY_FIELDS,incoming_fields=data.datas)
        is_owner=await ShopService(session=self.session).getby_shop_acc_id(account_id=account_id,shop_id=data.datas['shop_id'],timezone=TimeZoneEnum.Asia_Kolkata)
        if not is_owner:
            is_employee=await EmployeeRepo(session=self.session).is_employee_exists(employee_account_id=account_id,shop_id=data.datas['shop_id'])
            if not is_employee or is_employee['role']!=RoleEnum.SUPER_ADMIN.value:
                raise HTTPException(
                    status_code=400,
                    detail=ErrorResponseTypDict(
                        status_code=400,
                        msg="Error : Updating Employee",
                        description="Insufficient Permission",
                        success=False
                    )
                )
        
        data=data.datas

        saga_id:str=generate_uuid()
        saga_payload={'employees':data}
        r_key=generate_routingkey(domain=EMP_SERVICE_NAME,work_for=EMP_SERVICE_NAME,action=RoutingkeyActions.UPDATE,state=RoutingkeyState.REQUESTED,version=RoutingkeyVersions.V1)
        return await SagaProducer.emit(
            session=self.session,
            routing_key=r_key,
            exchange_name="employees.employees.accounts.exchange",
            saga_payload=CreateSagaStateSchema(
                id=saga_id,
                status=SagaStatusEnum.IN_PROGRESS,
                type=SagaTypeEnums.EMPLOYEE_UPDATED,
                steps={
                    f'accounts.{RoutingkeyActions.UPDATE.value}':SagaStepsValueEnum.PENDING
                },
                execution=SagaStateExecutionTypDict(
                    step="employees:update:requested",
                    service=f"{EMP_SERVICE_NAME.upper()}-SERVICE"
                ),
                data=saga_payload,
                error=None
            )
        )
    

    async def delete(self,shop_id:str,employee_id:str,account_id:str):
        res=await EmployeeService(session=self.session).delete(employee_id=employee_id,shop_id=shop_id,account_id=account_id)
        if res:
            await ReadDbEmployeeService(payload={},conditions={"employee_id":employee_id,'shop_id':shop_id}).delete()
            return SuccessResponseTypDict(
                detail=BaseResponseTypDict(
                    msg="Employee deleted successfully",
                    status_code=200,
                    success=True
                )
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
    
    async def get_all(self,q:str,limit:int,offset:int,timezone:TimeZoneEnum,read_db:Optional[bool]=True):
        res=await ReadDbEmployeeService(payload={},conditions={}).get(query=q,limit=limit,offset=offset)
        if not read_db:
            res=await EmployeeService(session=self.session).get(offset=offset,limit=limit,query=q,timezone=timezone)

        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                msg="Employees fetched successfully",
                status_code=200,
                success=True
            ),
            data=res
        )
    
    async def getby_id(self,employee_id:str,timezone:TimeZoneEnum,read_db:Optional[bool]=True):
        queries={
            "employee_id":employee_id.strip()
        }
        res=await ReadDbEmployeeService(payload={},conditions={}).get_one(queries=queries)
        if not read_db:
            res=await EmployeeService(session=self.session).getby_id(employee_id=employee_id,timezone=timezone)

        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                msg="Employee fetched successfully",
                status_code=200,
                success=True
            ),
            data=res
        )
    
    async def getby_shopid(self,shop_id:str,timezone:TimeZoneEnum,read_db:Optional[bool]=True):
        
        queries={
            'shop_id':shop_id.strip()
        }
        ic(queries)
        res=await ReadDbEmployeeService(payload={},conditions={}).getby_queries(queries=queries)
        if not read_db:
            res=await EmployeeService(session=self.session).getby_shopid(shop_id=shop_id,timezone=timezone)
        ic(res)
        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                msg="Employee fetched successfully",
                status_code=200,
                success=True
            ),
            data=res
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