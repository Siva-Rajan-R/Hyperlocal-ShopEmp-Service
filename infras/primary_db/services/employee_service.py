from icecream import ic
from ..repos.employee_repo import EmployeeRepo
from ..models.shop_model import Shops
from sqlalchemy import select,update,delete,or_,and_,func,String
from schemas.v1.db_schemas.employee_schemas import CreateEmployeeDbSchema,UpdateEmployeeDbSchema
from schemas.v1.request_schemas.employee_schemas import CreateEmployeeSchema,UpdateEmployeeSchema,DeleteEmployeeSchema,GetAllEmployeesSchema,GetEmployeeByIdSchema,GetEmployeeByShopIdSchema,VerifyEmployeeSchema
from models.service_models.base_service_model import BaseServiceModel
from core.decorators.error_handler_dec import catch_errors
from fastapi.exceptions import HTTPException
from hyperlocal_platform.core.enums.timezone_enum import TimeZoneEnum
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional,List,Union
from hyperlocal_platform.core.utils.uuid_generator import generate_uuid
from core.data_formats.enums.employee_enums import EmployeeDepartmentEnums,EmployeeRoleEnums
from hyperlocal_platform.core.decorators.db_session_handler_dec import start_db_transaction
from core.utils.token_utils import generate_verification_token, decode_verification_token
from core.utils.email_sender import send_verification_email
from integrations.utility_service import get_ui_id, get_shop_category, get_shop_unit
from hyperlocal_platform.core.models.req_res_models import SuccessResponseTypDict,BaseResponseTypDict,ErrorResponseTypDict
import httpx
from integrations.auth_service import get_or_create_user

async def _send_activity_log(shop_id: str, action: str, entity_id: str, description: str, changes: list = None, entity_name: str = ""):
    try:
        from messaging.main import RabbitMQMessagingConfig
        rabbitmq_msg_obj = RabbitMQMessagingConfig()
        await rabbitmq_msg_obj.publish_event(
            routing_key="activity_logs.routing.key",
            exchange_name="activity_logs.exchange",
            payload={
                "shop_id": shop_id,
                "user_name": "Hyperlocal-User",
                "service": "EMPLOYEE",
                "action": action,
                "entity_type": "EMPLOYEE",
                "entity_id": str(entity_id),
                "entity_name": str(entity_name),
                "description": description,
                "changes": changes or []
            },
            headers={}
        )
    except Exception as e:
        ic(f"Failed to log activity: {e}")


class EmployeeService(BaseServiceModel):
    def __init__(self, session:AsyncSession):
        super().__init__(session)
        self.employee_repo_obj=EmployeeRepo(session=session)


    async def create(self, data:CreateEmployeeSchema, owner_user_id:str)-> dict:
        employee_id=generate_uuid()
        shop_id = data.shop_id
        
        # Check in Authentication Service by email or mobile number
        user_id = None
        user_res=await get_or_create_user(email=data.email,mobile_number=data.mobile_number)
                    
        if user_res:
            user_id = user_res.get("user_id")
        else:
            raise HTTPException(status_code=400, detail="Could not resolve user ID from authentication service.")

        is_owner=(await self.session.execute(select(Shops.id).where(Shops.user_id==user_id))).mappings().all()
        ic(is_owner)
        if is_owner:
            raise HTTPException(
                status_code=400,
                detail=ErrorResponseTypDict(
                    msg="Error : Creating Employee",
                    description="Shop owner cannot be added as an employee",
                    success=False,
                    status_code=400
                )
            )

        existing_employee = await self.employee_repo_obj.is_employee_exists(employee_account_id=user_id, shop_id=shop_id)
        if existing_employee:
            raise HTTPException(
                status_code=400,
                detail=ErrorResponseTypDict(
                    msg="Error : Creating Employee",
                    description="User is already an employee of this shop",
                    success=False,
                    status_code=400
                )
            )
        
        ui_id=None
        ui_id_res = await get_ui_id(shop_id=data.shop_id)
        if isinstance(ui_id_res, dict) and "prefix" in ui_id_res:
            ui_id = f"{ui_id_res.get('prefix')}-{ui_id_res.get('current_number')}"
        # Add Employee Record
        data_toadd=CreateEmployeeDbSchema(
            id=employee_id,
            ui_id=ui_id,
            user_id=user_id,
            name=data.name,
            added_by=owner_user_id,
            shop_id=shop_id,
            role=data.role,
            joined_date=data.joined_date,
            department=data.department,
            accepted=False,
            additional_infos=data.additional_infos
        )
        res=await self.employee_repo_obj.create(data=data_toadd)
        if res:
            try:
                from ...read_db.services.employee_service import ReadDbEmployeeService
                from ...read_db.models.employee_model import ReadDbEmployeeCreateModel
                mongo_payload = ReadDbEmployeeCreateModel(
                    employee_id=res["id"],
                    user_id=res["user_id"],
                    shop_id=res["shop_id"],
                    name=res["name"],
                    email=data.email,
                    mobile_number=data.mobile_number,
                    is_accepted=res["accepted"],
                    added_by=res["added_by"],
                    role=res["role"],
                    joined_date=str(res["joined_date"]),
                    department=res["department"],
                    additional_infos=res.get("additional_infos") or {}
                )
                await ReadDbEmployeeService(payload=mongo_payload).create()
            except Exception as e:
                ic(f"Failed to sync employee to MongoDB: {e}")

            token = generate_verification_token(employee_id=employee_id, shop_id=shop_id)
            await send_verification_email(email=data.email, name=data.name, token=token)

            await _send_activity_log(
                shop_id=shop_id,
                action="CREATED",
                entity_id=employee_id,
                entity_name=str(data.name),
                description=f"Created Employee {data.name} ({employee_id})",
                changes=[]
            )
        return res


    async def update(self, data:UpdateEmployeeSchema) -> dict | None:
        old_employee = await self.employee_repo_obj.getby_id(GetEmployeeByIdSchema(id=data.id, shop_id=data.shop_id))
        ic(old_employee)
        
        # Merge optional updates into additional_infos
        additional_infos = {}
        if data.additional_infos:
            additional_infos = data.additional_infos.model_dump(exclude_unset=True) if hasattr(data.additional_infos, 'model_dump') else data.additional_infos

        data_toupdate=UpdateEmployeeDbSchema(additional_infos=additional_infos,**data.model_dump(mode="json",exclude={'additional_infos'},exclude_none=True,exclude_unset=True))

        res=await self.employee_repo_obj.update(data=data_toupdate)
        if res:
            try:
                from ...read_db.services.employee_service import ReadDbEmployeeService
                from ...read_db.models.employee_model import ReadDbEmployeeUpdateModel
                mongo_update = ReadDbEmployeeUpdateModel(
                    name=res.get("name"),
                    role=res.get("role"),
                    joined_date=str(res.get("joined_date")) if res.get("joined_date") else None,
                    department=res.get("department"),
                    additional_infos=res.get("additional_infos") or {}
                )
                await ReadDbEmployeeService(
                    payload=mongo_update,
                    conditions={"employee_id": data.id, "shop_id": data.shop_id}
                ).update()
            except Exception as e:
                ic(f"Failed to sync employee update to MongoDB: {e}")

            try:
                def _is_empty_or_none(val):
                    if val is None: return True
                    if isinstance(val, (dict, list, set, str, tuple)) and len(val) == 0: return True
                    return str(val).strip() in ("None", "{}", "[]", "", "null", "NoneType")

                dumped_updates = data.model_dump(exclude_unset=True, exclude_none=True)
                changes = []
                for key, new_val in dumped_updates.items():
                    if key in ["id", "shop_id", "user_id", "cur_user_id"]:
                        continue
                    prev_val = old_employee.get(key) if old_employee else None
                    if _is_empty_or_none(prev_val) and _is_empty_or_none(new_val):
                        continue
                    if prev_val != new_val and str(prev_val).strip() != str(new_val).strip():
                        changes.append({
                            "field": key,
                            "before": str(prev_val) if prev_val is not None else "None",
                            "after": str(new_val) if new_val is not None else "None"
                        })
                emp_name = res.get("name") or (old_employee.get("name") if old_employee else "Employee")
                await _send_activity_log(
                    shop_id=data.shop_id,
                    action="UPDATED",
                    entity_id=data.id,
                    entity_name=str(emp_name),
                    description=f"Updated Employee {emp_name} ({data.id})",
                    changes=changes
                )
            except Exception as log_err:
                ic(f"Failed to send employee update log: {log_err}")
        return res

    async def delete(self,data:DeleteEmployeeSchema)-> dict | None:
        old_employee = await self.employee_repo_obj.getby_id(GetEmployeeByIdSchema(id=data.id, shop_id=data.shop_id))
        res=await self.employee_repo_obj.delete(data=data)
        if res:
            try:
                from ...read_db.services.employee_service import ReadDbEmployeeService
                await ReadDbEmployeeService(
                    conditions={"employee_id": data.id, "shop_id": data.shop_id}
                ).delete()
            except Exception as e:
                ic(f"Failed to sync employee deletion to MongoDB: {e}")

            employee_name = old_employee.get('name', 'Employee') if old_employee else 'Employee'
            await _send_activity_log(
                shop_id=data.shop_id,
                action="DELETED",
                entity_id=data.id,
                entity_name=str(employee_name),
                description=f"Deleted Employee {employee_name} ({data.id})",
                changes=[]
            )
        return res
    

    async def get(self,data:GetAllEmployeesSchema)-> dict:
        try:
            from ...read_db.services.employee_service import ReadDbEmployeeService
            read_service = ReadDbEmployeeService(payload=None, conditions={})
            res = await read_service.get(query=data.query, limit=data.limit, offset=data.offset)
        except Exception as e:
            ic(f"Failed to fetch employees from MongoDB: {e}")
            res = None
        
        if not res:
            res=await self.employee_repo_obj.get(data=data)
        
        if data.offset in (0, 1):
            overall_values = await self.employee_repo_obj.get_overall_values(data=data)
            return {
                "overall_datas": overall_values,
                "datas": res
            }

        return {"datas": res}
        
    

    async def getby_id(self,data:GetEmployeeByIdSchema)-> dict | None:
        try:
            from ...read_db.services.employee_service import ReadDbEmployeeService
            read_service = ReadDbEmployeeService(payload=None, conditions={"employee_id": data.id, "shop_id": data.shop_id})
            res = await read_service.get_one(queries={"employee_id": data.id, "shop_id": data.shop_id})
        except Exception as e:
            ic(f"Failed to fetch employee from MongoDB: {e}")
            res = None

        if not res:
            res=await self.employee_repo_obj.getby_id(data=data)
        return res

    

    async def getby_shopid(self,data:GetEmployeeByShopIdSchema)-> dict:
        try:
            from ...read_db.services.employee_service import ReadDbEmployeeService
            read_service = ReadDbEmployeeService(payload=None, conditions={})
            if data.query:
                res = await read_service.get(query=data.query, limit=data.limit, offset=data.offset)
            else:
                res = await read_service.getby_queries(queries={"shop_id": data.shop_id}, limit=data.limit, offset=data.offset)
        except Exception as e:
            ic(f"Failed to fetch employees from MongoDB: {e}")
            res = None
        
        if not res:
            res=await self.employee_repo_obj.getby_shopid(data=data)
        
        if data.offset in (0, 1):
            overall_values = await self.employee_repo_obj.get_overall_values(data=data)
            return {
                "overall_datas": overall_values,
                "datas": res
            }
            
        return {"datas": res}
    

    async def verify_employee(self,data:VerifyEmployeeSchema)->dict:
        if not data.employee_id and not data.mobile_number and not data.email:
            return {'id':'','exists':False}
        
        res=await self.employee_repo_obj.verify_employee(data=data)
        return res
    
    async def accept_employee(self, token: str) -> dict:
        payload = decode_verification_token(token)
        if not payload:
            raise HTTPException(status_code=400, detail="Invalid or expired verification token")
        
        employee_id = payload.get("employee_id")
        shop_id = payload.get("shop_id")
        
        success = await self.employee_repo_obj.accept_employee(employee_id=employee_id, shop_id=shop_id)
        if not success:
            raise HTTPException(status_code=404, detail="Employee invitation record not found")
        
        try:
            from ...read_db.services.employee_service import ReadDbEmployeeService
            from ...read_db.models.employee_model import ReadDbEmployeeUpdateModel
            await ReadDbEmployeeService(
                payload=ReadDbEmployeeUpdateModel(is_accepted=True),
                conditions={"employee_id": employee_id, "shop_id": shop_id}
            ).update()
        except Exception as e:
            ic(f"Failed to sync acceptance to MongoDB: {e}")
        
        return {"success": True, "employee_id": employee_id, "shop_id": shop_id}

    async def search(self, query:str, limit:int):
        """This is just a wrapper for ABC(Abstract Class) of BaseService"""
        ...
