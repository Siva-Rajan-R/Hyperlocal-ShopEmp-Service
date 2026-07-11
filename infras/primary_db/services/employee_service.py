from icecream import ic
from ..repos.employee_repo import EmployeeRepo
from .user_service import UserService
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
import httpx

ACTIVITY_LOG_URL = "http://127.0.0.1:8001/activity-logs"

async def _send_activity_log(shop_id: str, action: str, entity_id: str, description: str, changes: list = None):
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(ACTIVITY_LOG_URL, json={
                "shop_id": shop_id,
                "user_name": "siva",
                "service": "Employee",
                "action": action,
                "entity_type": "Employee",
                "entity_id": entity_id,
                "description": description,
                "changes": changes or []
            })
    except Exception as e:
        ic(f"Failed to log activity: {e}")


class EmployeeService(BaseServiceModel):
    def __init__(self, session:AsyncSession):
        super().__init__(session)
        self.employee_repo_obj=EmployeeRepo(session=session)
        self.user_service_obj=UserService(session=session)


    async def create(self, data:CreateEmployeeSchema, owner_user_id:str)-> dict:
        employee_id=generate_uuid()
        shop_id = data.shop_id
        
        # 1. Create or get user record first
        user = await self.user_service_obj.get_or_create_user(
            name=data.name,
            email=data.email,
            mobile_number=data.mobile_number
        )
        user_id = user['id']

        # from infras.read_db.repos.shopidconfig_repo import ShopIdConfigReadDbRepo
        # from core.utils.id_formatter import format_ui_id
        
        # shop_config = await ShopIdConfigReadDbRepo.get_config(shop_id)
        # emp_config = shop_config.get("employee", {})
        # prefix = emp_config.get("prefix", "EMP")
        # start_from = emp_config.get("start_from", 1)
        
        # raw_sequence = await self.employee_repo_obj.get_next_sequence(shop_id, start_from)
        # ui_id_str = format_ui_id(prefix, start_from, raw_sequence)
        ui_id=None
        ui_id_res = await get_ui_id(shop_id=data.shop_id)
        if isinstance(ui_id_res, dict) and "prefix" in ui_id_res:
            ui_id = f"{ui_id_res.get('prefix')}-{ui_id_res.get('current_number')}"
        else:
            return False

        # 2. Add Employee Record
        data_toadd=CreateEmployeeDbSchema(
            id=employee_id,
            ui_id=ui_id,
            user_id=user_id,
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
            # 3. Generate verification token and send email
            token = generate_verification_token(employee_id=employee_id, shop_id=shop_id)
            await send_verification_email(email=data.email, name=data.name, token=token)

            await _send_activity_log(
                shop_id=shop_id,
                action="CREATE",
                entity_id=employee_id,
                description=f"Created and invited new employee: {data.name}",
                changes=[{"field": "name", "before": "", "after": str(data.name)}]
            )
        return res


    async def update(self, data:UpdateEmployeeSchema) -> dict | None:
        old_employee = await self.employee_repo_obj.getby_id(GetEmployeeByIdSchema(id=data.id, shop_id=data.shop_id))
        ic(old_employee)
        
        # Merge optional updates into additional_infos
        additional_infos = {}
        if data.datas:
            additional_infos = data.datas.model_dump(exclude_unset=True)

        data_toupdate=UpdateEmployeeDbSchema(additional_infos=additional_infos,**data.model_dump(mode="json",exclude=['additional_infos'],exclude_none=True,exclude_unset=True))

        res=await self.employee_repo_obj.update(data=data_toupdate)
        # if res and old_employee:
        #     changes_list = []
        #     desc_changes = []
        #     dump_data = data.model_dump(exclude_unset=True, exclude_none=True)
        #     for k, v in dump_data.items():
        #         if k not in ["id", "shop_id"] and k in old_employee and str(old_employee[k]) != str(v):
        #             desc_changes.append(f"{k} prv({old_employee[k]}) after ({v})")
        #             changes_list.append({"field": k, "before": str(old_employee[k]), "after": str(v)})
        #     if desc_changes:
        #         await _send_activity_log(
        #             shop_id=data.shop_id,
        #             action="UPDATE",
        #             entity_id=data.id,
        #             description=f"Updated employee: {', '.join(desc_changes)}",
        #             changes=changes_list
        #         )
        return res

    async def delete(self,data:DeleteEmployeeSchema)-> dict | None:
        old_employee = await self.employee_repo_obj.getby_id(GetEmployeeByIdSchema(id=data.id, shop_id=data.shop_id))
        res=await self.employee_repo_obj.delete(data=data)
        if res:
            employee_name = old_employee.get('name', 'Unknown') if old_employee else 'Unknown'
            await _send_activity_log(
                shop_id=data.shop_id,
                action="DELETE",
                entity_id=data.id,
                description=f"Deleted employee: {employee_name}",
                changes=[{"field": "name", "before": str(employee_name), "after": "DELETED"}]
            )
        return res
    

    async def get(self,data:GetAllEmployeesSchema)-> dict:
        res=await self.employee_repo_obj.get(data=data)
        
        if data.offset in (0, 1):
            overall_values = await self.employee_repo_obj.get_overall_values(data=data)
            return {
                "overall_datas": overall_values,
                "datas": res
            }

        return {"datas": res}
        
    

    async def getby_id(self,data:GetEmployeeByIdSchema)-> dict | None:
        res=await self.employee_repo_obj.getby_id(data=data)
        return res

    

    async def getby_shopid(self,data:GetEmployeeByShopIdSchema)-> dict:
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
        
        return {"success": True, "employee_id": employee_id, "shop_id": shop_id}

    async def search(self, query:str, limit:int):
        """This is just a wrapper for ABC(Abstract Class) of BaseService"""
        ...
