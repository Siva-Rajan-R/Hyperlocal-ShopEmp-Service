import os
from core.utils.user_context import get_activity_log_user_info
from icecream import ic
from infras.primary_db.repos.employee_repo import EmployeeRepo
from infras.primary_db.models.shop_model import Shops
from infras.primary_db.models.employee_model import Employees
from sqlalchemy import select, desc,update,delete,or_,and_,func,String
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


async def _send_activity_log(shop_id: str, action: str, entity_id: str, description: str, changes: list = None, entity_name: str = ""):
    try:
        from messaging.main import RabbitMQMessagingConfig
        rabbitmq_msg_obj = RabbitMQMessagingConfig()
        await rabbitmq_msg_obj.publish_event(
            routing_key="activity_logs.routing.key",
            exchange_name="activity_logs.exchange",
            payload={
                "shop_id": shop_id,
                **get_activity_log_user_info(),
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
        mock_expired = os.getenv("MOCK_SUBSCRIPTION_EXPIRED", "false").lower() in ("true", "1", "yes")
        if mock_expired:
            raise HTTPException(
                status_code=403,
                detail=ErrorResponseTypDict(
                    msg="Subscription Expired",
                    description="Your subscription has expired. Adding new staff/users is paused until subscription is renewed.",
                    success=False,
                    status_code=403
                )
            )

        shop_id = data.shop_id
        from infras.primary_db.models.subscription_model import ShopSubscriptions
        from infras.primary_db.models.shop_model import Shops

        # Find shop owner user_id
        shop_stmt = select(Shops).where(Shops.id == shop_id)
        shop_obj = (await self.session.execute(shop_stmt)).scalar_one_or_none()
        owner_id = shop_obj.user_id if shop_obj else owner_user_id

        # Count all employees across all shops owned by this user account
        owner_shops_subquery = select(Shops.id).where(Shops.user_id == owner_id)
        total_emp_stmt = select(func.count(Employees.id)).where(Employees.shop_id.in_(owner_shops_subquery))
        total_user_count = (await self.session.execute(total_emp_stmt)).scalar() or 0

        # Check user's subscription
        sub_stmt = select(ShopSubscriptions).join(Shops, ShopSubscriptions.shop_id == Shops.id).where(Shops.user_id == owner_id).order_by(desc(ShopSubscriptions.created_at)).limit(1)
        user_sub = (await self.session.execute(sub_stmt)).scalar_one_or_none()
        if not user_sub:
            sub_stmt2 = select(ShopSubscriptions).where(ShopSubscriptions.shop_id == shop_id).order_by(desc(ShopSubscriptions.created_at)).limit(1)
            user_sub = (await self.session.execute(sub_stmt2)).scalar_one_or_none()

        mock_expired = os.getenv("MOCK_SUBSCRIPTION_EXPIRED", "false").lower() == "true"
        if mock_expired or (user_sub and user_sub.status == "expired"):
            raise HTTPException(
                status_code=403,
                detail=ErrorResponseTypDict(
                    msg="Subscription Expired",
                    description="Your subscription has expired. Adding new staff/users is paused until subscription is renewed.",
                    success=False,
                    status_code=403
                )
            )

        max_users = user_sub.max_users if user_sub else 2
        if total_user_count >= max_users:
            raise HTTPException(
                status_code=403,
                detail=ErrorResponseTypDict(
                    msg="User Limit Reached",
                    description=f"User limit reached ({total_user_count}/{max_users} users). Please upgrade your plan or add an Extra User add-on.",
                    success=False,
                    status_code=403
                )
            )

        employee_id=generate_uuid()
        
        # Check in Authentication Service by email or mobile number
        user_id = None
        temp_password = None
        from integrations.auth_service import get_user_info
        user_res=await get_user_info(email=data.email,mobile_number=data.mobile_number)
                    
        if user_res:
            user_id = user_res.get("user_id")
        else:
            user_id = str(generate_uuid())

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
        # Store email and mobile in additional_infos so it is always retrievable
        stored_additional_infos = dict(data.additional_infos or {})
        if data.email:
            stored_additional_infos["email"] = data.email
        if data.mobile_number:
            stored_additional_infos["mobile_number"] = data.mobile_number

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
            additional_infos=stored_additional_infos
        )
        res=await self.employee_repo_obj.create(data=data_toadd)
        if res:
            try:
                from infras.read_db.services.employee_service import ReadDbEmployeeService
                from infras.read_db.models.employee_model import ReadDbEmployeeCreateModel
                mongo_payload = ReadDbEmployeeCreateModel(
                    employee_id=res["id"],
                    ui_id=res.get("ui_id"),
                    user_id=res["user_id"],
                    shop_id=res["shop_id"],
                    name=res["name"],
                    email=data.email,
                    mobile_number=data.mobile_number,
                    accepted=res["accepted"],
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
            await send_verification_email(email=data.email, name=data.name, token=token, temp_password=temp_password)

            await _send_activity_log(
                shop_id=shop_id,
                action="CREATED",
                entity_id=employee_id,
                entity_name=str(data.name),
                description=f"Created Employee {data.name} ({employee_id})",
                changes=[]
            )
        return res

    async def create_bulk(self, data: List[CreateEmployeeSchema], owner_user_id: str) -> List[dict]:
        results = []
        for item in data:
            try:
                res = await self.create(data=item, owner_user_id=owner_user_id)
                if res:
                    results.append(res)
            except Exception as e:
                ic(f"Error creating bulk employee item: {e}")
        return results



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
                from infras.read_db.services.employee_service import ReadDbEmployeeService
                from infras.read_db.models.employee_model import ReadDbEmployeeUpdateModel
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

    async def delete(self, data: DeleteEmployeeSchema) -> dict | None:
        old_employee = await self.employee_repo_obj.getby_id(GetEmployeeByIdSchema(id=data.id, shop_id=data.shop_id))
        res = await self.employee_repo_obj.delete(data=data)
        
        # Always delete from MongoDB Read DB
        mongo_doc = None
        try:
            from infras.read_db.services.employee_service import ReadDbEmployeeService
            read_emp_service = ReadDbEmployeeService(
                payload=None,
                conditions={"$or": [{"employee_id": data.id}, {"id": data.id}], "shop_id": data.shop_id}
            )
            mongo_doc = await read_emp_service.get_one(queries={"$or": [{"employee_id": data.id}, {"id": data.id}]})
            await read_emp_service.delete()
        except Exception as e:
            ic(f"Failed to sync employee deletion to MongoDB: {e}")

        if not res and not mongo_doc:
            return None

        employee_name = (res.get("name") if res else None) or (old_employee.get('name') if old_employee else None) or (mongo_doc.get("name") if mongo_doc else "Employee")

        try:
            await _send_activity_log(
                shop_id=data.shop_id,
                action="DELETED",
                entity_id=data.id,
                entity_name=str(employee_name),
                description=f"Deleted Employee {employee_name} ({data.id})",
                changes=[]
            )
        except Exception as log_err:
            ic(f"Failed to send employee deletion log: {log_err}")

        return res or mongo_doc or {"id": data.id, "shop_id": data.shop_id, "name": employee_name}
    

    async def get(self,data:GetAllEmployeesSchema)-> dict:
        try:
            from infras.read_db.services.employee_service import ReadDbEmployeeService
            read_service = ReadDbEmployeeService(payload=None, conditions={})
            res = await read_service.get(query=data.query, limit=data.limit, offset=data.offset)
        except Exception as e:
            ic(f"Failed to fetch employees from MongoDB: {e}")
            res = None
        
        if not res:
            res=await self.employee_repo_obj.get(data=data)
        
        if res and isinstance(res, list):
            for item in res:
                item["id"] = item.get("id") or item.get("employee_id")
                item["employee_id"] = item.get("employee_id") or item.get("id")

        if data.offset in (0, 1):
            overall_values = await self.employee_repo_obj.get_overall_values(data=data)
            return {
                "overall_datas": overall_values,
                "datas": res
            }

        return {"datas": res}
        
    

    async def getby_id(self,data:GetEmployeeByIdSchema)-> dict | None:
        try:
            from infras.read_db.services.employee_service import ReadDbEmployeeService
            read_service = ReadDbEmployeeService(payload=None, conditions={"employee_id": data.id, "shop_id": data.shop_id})
            res = await read_service.get_one(queries={"$or": [{"employee_id": data.id}, {"id": data.id}], "shop_id": data.shop_id})
        except Exception as e:
            ic(f"Failed to fetch employee from MongoDB: {e}")
            res = None

        if not res:
            res=await self.employee_repo_obj.getby_id(data=data)

        if res:
            res["id"] = res.get("id") or res.get("employee_id")
            res["employee_id"] = res.get("employee_id") or res.get("id")

            # Ensure ui_id is present
            if not res.get("ui_id"):
                pg_res = await self.employee_repo_obj.getby_id(data=data)
                if pg_res and pg_res.get("ui_id"):
                    res["ui_id"] = pg_res.get("ui_id")

            # Attach shop_name if shop exists
            if res.get("shop_id"):
                try:
                    from infras.primary_db.repos.shop_repo import ShopRepo
                    from schemas.v1.request_schemas.shop_schemas import GetShopByIdSchema
                    shop_doc = await ShopRepo(session=self.session).getby_id(GetShopByIdSchema(shop_id=res["shop_id"]))
                    if shop_doc:
                        res["shop_name"] = shop_doc.get("name")
                except Exception as se:
                    ic(f"Failed to fetch shop name: {se}")

        return res

    

    async def getby_shopid(self,data:GetEmployeeByShopIdSchema)-> dict:
        try:
            from infras.read_db.services.employee_service import ReadDbEmployeeService
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

        if res and isinstance(res, list):
            for item in res:
                item["id"] = item.get("id") or item.get("employee_id")
                item["employee_id"] = item.get("employee_id") or item.get("id")
        
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
        
        # 1. Fetch employee record from Postgres
        from schemas.v1.request_schemas.employee_schemas import GetEmployeeByIdSchema
        employee_data = await self.employee_repo_obj.getby_id(GetEmployeeByIdSchema(id=employee_id, shop_id=shop_id))
        
        # If not found in Postgres, check MongoDB
        mongo_emp = None
        try:
            from infras.read_db.services.employee_service import ReadDbEmployeeService
            read_emp_service = ReadDbEmployeeService(payload=None, conditions={})
            mongo_emp = await read_emp_service.get_one(queries={"$or": [{"employee_id": employee_id}, {"id": employee_id}]})
        except Exception as me:
            ic(f"MongoDB employee lookup note: {me}")

        if not employee_data and not mongo_emp:
            raise HTTPException(status_code=404, detail="Employee invitation record not found")

        # If it was in Mongo but missing from Postgres, restore into Postgres
        if not employee_data and mongo_emp:
            try:
                from schemas.v1.db_schemas.employee_schemas import CreateEmployeeDbSchema
                from datetime import datetime, date
                joined_d = date.today()
                if mongo_emp.get("joined_date"):
                    try:
                        joined_d = datetime.fromisoformat(str(mongo_emp["joined_date"]).split(" ")[0]).date()
                    except Exception:
                        pass
                
                reconstruct_schema = CreateEmployeeDbSchema(
                    id=employee_id,
                    ui_id=mongo_emp.get("ui_id"),
                    user_id=mongo_emp.get("user_id"),
                    name=mongo_emp.get("name", "Employee"),
                    added_by=mongo_emp.get("added_by", ""),
                    shop_id=shop_id,
                    role=mongo_emp.get("role", "STAFF"),
                    joined_date=joined_d,
                    department=mongo_emp.get("department"),
                    accepted=False,
                    additional_infos=mongo_emp.get("additional_infos") or {}
                )
                employee_data = await self.employee_repo_obj.create(data=reconstruct_schema)
            except Exception as re_err:
                ic(f"Failed to restore employee to Postgres: {re_err}")

        employee_dict = dict(employee_data) if employee_data else dict(mongo_emp or {})
        
        # Fetch shop name
        shop_name = "Retail Store"
        try:
            from infras.primary_db.repos.shop_repo import ShopRepo
            from schemas.v1.request_schemas.shop_schemas import GetShopByIdSchema
            shop_doc = await ShopRepo(session=self.session).getby_id(GetShopByIdSchema(shop_id=shop_id))
            if shop_doc and shop_doc.get("name"):
                shop_name = shop_doc.get("name")
        except Exception as se:
            ic(f"Failed to fetch shop name: {se}")

        # 2. Extract email & mobile from MongoDB or Postgres additional_infos
        email = None
        mobile_number = None
        try:
            from infras.read_db.services.employee_service import ReadDbEmployeeService
            read_emp_service = ReadDbEmployeeService(payload=None, conditions={})
            mongo_emp = await read_emp_service.get_one(queries={"$or": [{"employee_id": employee_id}, {"id": employee_id}]})
            if mongo_emp:
                email = mongo_emp.get("email")
                mobile_number = mongo_emp.get("mobile_number")
        except Exception as me:
            ic(f"MongoDB employee lookup note: {me}")

        # Fallback to Postgres additional_infos
        add_infos = employee_dict.get("additional_infos") or {}
        if not email and isinstance(add_infos, dict):
            email = add_infos.get("email")
        if not mobile_number and isinstance(add_infos, dict):
            mobile_number = add_infos.get("mobile_number")

        # If already accepted, return success idempotently
        if employee_dict.get("accepted"):
            return {
                "success": True,
                "employee_id": employee_id,
                "shop_id": shop_id,
                "email": email,
                "has_credentials": False
            }

        employee_name = employee_dict.get("name") or "Employee"
        role = employee_dict.get("role") or "STAFF"
        
        # 3. Check Auth-Service
        final_user_id = employee_dict.get("user_id")
        temp_password = None
        
        try:
            from integrations.auth_service import get_user_info, create_user_with_id
            if email or mobile_number:
                existing_user = await get_user_info(email=email, mobile_number=mobile_number)
                if existing_user:
                    final_user_id = existing_user.get("user_id") or final_user_id
                else:
                    import secrets
                    import string
                    rand_chars = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(8))
                    generated_pwd = f"Emp@{rand_chars}"
                    
                    await create_user_with_id(
                        email=email,
                        mobile_number=mobile_number,
                        user_id=final_user_id,
                        password=generated_pwd
                    )
                    temp_password = generated_pwd
        except Exception as auth_err:
            ic(f"Auth Service provisioning note in accept_employee: {auth_err}")
        
        # 4. Accept employee and update user_id in Postgres
        success = await self.employee_repo_obj.accept_employee(employee_id=employee_id, shop_id=shop_id, user_id=final_user_id)
        if not success:
            raise HTTPException(status_code=404, detail="Failed to accept employee in database")
        
        # 5. Sync to MongoDB
        try:
            from infras.read_db.services.employee_service import ReadDbEmployeeService
            from infras.read_db.models.employee_model import ReadDbEmployeeUpdateModel
            await ReadDbEmployeeService(
                payload=ReadDbEmployeeUpdateModel(accepted=True, user_id=final_user_id),
                conditions={"$or": [{"employee_id": employee_id}, {"id": employee_id}]}
            ).update()
        except Exception as e:
            ic(f"Failed to sync acceptance to MongoDB: {e}")

        # 6. Send credentials email to the employee
        if email:
            try:
                from core.utils.email_sender import send_employee_credentials_email
                from core.configs.settings_config import SETTINGS
                login_url = f"{SETTINGS.FRONTEND_BASE_URL}/login" if hasattr(SETTINGS, 'FRONTEND_BASE_URL') and SETTINGS.FRONTEND_BASE_URL else "http://localhost:5173/login"
                await send_employee_credentials_email(
                    email=email,
                    name=employee_name,
                    password=temp_password,
                    shop_name=shop_name,
                    role=role,
                    login_url=login_url
                )
                ic(f"Sent employee credentials email to {email}")
            except Exception as mail_err:
                ic(f"Failed to send credentials email to employee {email}: {mail_err}")
        
        return {
            "success": True,
            "employee_id": employee_id,
            "shop_id": shop_id,
            "email": email,
            "has_credentials": bool(temp_password),
            "shop_name": shop_name
        }

    async def search(self, query:str, limit:int):
        """This is just a wrapper for ABC(Abstract Class) of BaseService"""
        ...
