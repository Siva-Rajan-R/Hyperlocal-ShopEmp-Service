from infras.primary_db.services.employee_service import EmployeeService
from infras.primary_db.main import AsyncSession,AsyncShopEmployeeLocalSession
from schemas.v1.request_schemas.employee_schema import CreateEmployeeSchema,UpdateEmployeeSchema
from hyperlocal_platform.core.enums.saga_state_enum import SagaStatusEnum
from icecream import ic
from core.decorators.error_handler_dec import catch_errors
from models.messaging_models.consumer_model import BaseConsumerModel
from hyperlocal_platform.infras.saga.schemas import CreateSagaStateSchema,UpdateSagaStateSchema
from hyperlocal_platform.infras.saga.repo import SagaStatesRepo,SagaStatusEnum
from core.errors.messaging_errors import BussinessError,FatalError,RetryableError
from hyperlocal_platform.core.constants import MAX_RETRY_COUNT
from ..main import RabbitMQMessagingConfig
from hyperlocal_platform.core.enums.error_enums import ErrorTypeSEnum
from hyperlocal_platform.core.typed_dicts.messaging_typdict import EventPublishingTypDict,SuccessMessagingTypDict
from hyperlocal_platform.core.typed_dicts.saga_status_typ_dict import SagaStateErrorTypDict
from hyperlocal_platform.core.utils.routingkey_builder import generate_routingkey,RoutingkeyActions,RoutingkeyState,RoutingkeyVersions
from core.utils.exception_serializer import serialize_exception
from infras.read_db.models.employee_model import ReadDbEmployeeCreateModel,ReadDbEmployeeUpdateModel,ReadDbEmployeeReadModel
from hyperlocal_platform.core.basemodels.readdb_model import ReadDbBaseModel



class AccountsConsumer(BaseConsumerModel):
    async def create(self)->SuccessMessagingTypDict:
        is_new=False
        compensation_payload:EventPublishingTypDict=EventPublishingTypDict(
            exchange_name="employees.employees.accounts.exchange",
            routing_key=generate_routingkey(domain="employees",work_for="employees",action=RoutingkeyActions.CREATE,state=RoutingkeyState.FAILED,version=RoutingkeyVersions.V1),
            payload={},
            headers={
                'saga_id':self.saga_id
            }
        )
        try:
            async with AsyncShopEmployeeLocalSession() as session:
                ic(f"Employee-Create : Headers=> {self.headers}, Payload => {self.payload} ")
                
                event_data:dict=self.payload['data']
                accounts_data:dict=event_data.get("accounts")
                employees_data:dict=event_data.get("employees")
                employess_base_datas:dict=employees_data.get("datas")
                if not accounts_data or not employees_data:
                    raise BussinessError(
                        type=ErrorTypeSEnum.BUSSINESS_ERROR,
                        error=SagaStateErrorTypDict(
                            code=ErrorTypeSEnum.BUSSINESS_ERROR.value,
                            debug="There is not accounts or employee data found on the payload",
                            user_msg="Something went wrong, please try again"
                        ),
                        compensation=True,
                        compensation_payload=compensation_payload
                    )
                
                is_new=accounts_data['is_new']
                
                data=CreateEmployeeSchema(**employees_data)
                res=await EmployeeService(session=session).create(
                    data=data,
                    account_id=employees_data['account_id'],
                    account_info=accounts_data
                )

                ic(res)
                if not res:
                    ic("Employee creation failed")
                    raise BussinessError(
                        type=ErrorTypeSEnum.BUSSINESS_ERROR,
                        error=SagaStateErrorTypDict(
                            debug="Invalid payload for employee creation, may be a mistmatch of (account id,employee datas) or employee already exists",
                            user_msg="Invalid employee payloads or employee already exists",
                            code=ErrorTypeSEnum.BUSSINESS_ERROR.value
                        ),
                        compensation=is_new,
                        compensation_payload=compensation_payload
                    )
                
                readdb_data=ReadDbEmployeeCreateModel(
                    employee_id=res.id,
                    account_id=accounts_data['id'],
                    shop_id=employees_data['shop_id'],
                    email=employess_base_datas['email'],
                    name=employess_base_datas['name'],
                    mobile_number=employess_base_datas['mobile_number'],
                    role=employess_base_datas['role'],
                    is_accepted=False,
                    added_by=accounts_data['owner_name'],

                )

                return SuccessMessagingTypDict(
                    read_db=ReadDbBaseModel(
                        payload=readdb_data,
                        method="create"
                    ),
                    response=res,
                    mark_completed=True
                )
            
        except (BussinessError,RetryableError,FatalError):
            raise

        except Exception as e:
            raise FatalError(
                type=ErrorTypeSEnum.FATAL_ERROR,
                error=SagaStateErrorTypDict(
                    code=ErrorTypeSEnum.FATAL_ERROR.value,
                    debug=serialize_exception(e),
                    user_msg="We are facing some internal problem please try again"
                ),
                compensation_payload=compensation_payload,
                compensation=True
            )

    
    async def update(self)->SuccessMessagingTypDict:
        compensation_payload=EventPublishingTypDict(
            exchange_name="employees.employees.accounts.exchange",
            routing_key=generate_routingkey(domain="employees",work_for="employees",action=RoutingkeyActions.UPDATE,state=RoutingkeyState.FAILED,version=RoutingkeyVersions.V1),
            payload={},
            headers={'saga_id':self.saga_id}
        )
        async with AsyncShopEmployeeLocalSession() as session:
            ic(f"Employee-Update : Headers=> {self.headers}, Payload => {self.payload} ")
            event_data:dict=self.payload['data']
            accounts_data:dict=event_data.get("accounts")
            employees_data:dict=event_data.get("employees")
            employess_base_datas:dict=employees_data.get("datas")
            if not accounts_data or not employees_data:
                raise BussinessError(
                    type=ErrorTypeSEnum.BUSSINESS_ERROR,
                    error=SagaStateErrorTypDict(
                        code=ErrorTypeSEnum.BUSSINESS_ERROR.value,
                        debug="There is not accounts or employee data found on the payload",
                        user_msg="Something went wrong, please try again"
                    ),
                    compensation=True,
                    compensation_payload=compensation_payload
                )
            
            
            data=UpdateEmployeeSchema(**employees_data)
            res=await EmployeeService(session=session).update(
                data=data,
                account_info=accounts_data
            )

            if not res:
                ic("Employee creation failed")
                raise BussinessError(
                    type=ErrorTypeSEnum.BUSSINESS_ERROR,
                    error=SagaStateErrorTypDict(
                        user_msg="Invalid employee payload or employee not found",
                        debug="Invalid payload for employee creation , may be it occurs due to invalid (employee_id,shop_id) or employee not found",
                        code=ErrorTypeSEnum.BUSSINESS_ERROR.value
                    )
                )
            ic(employess_base_datas)
            readdb_data=ReadDbEmployeeUpdateModel(
                name=employess_base_datas['name'],
                is_accepted=employess_base_datas['is_accepted'],
                role=employess_base_datas['role'],
                mobile_number=employess_base_datas['mobile_number']

            )

            return SuccessMessagingTypDict(
                read_db=ReadDbBaseModel(
                    payload=readdb_data,
                    method="update",
                    condition={'employee_id':employees_data['id'],'account_id':employees_data['account_id']}
                ),
                response=res,
                mark_completed=True
            )
            
    

    async def delete(self):
        ...