from ..models.employee_model import Employees
from sqlalchemy import select,update,delete,or_,and_,func,String
from sqlalchemy.dialects.postgresql import insert
from schemas.v1.db_schemas.employee_schemas import CreateEmployeeDbSchema,UpdateEmployeeDbSchema
from schemas.v1.request_schemas.employee_schemas import DeleteEmployeeSchema,GetAllEmployeesSchema,GetEmployeeByIdSchema,GetEmployeeByShopIdSchema,VerifyEmployeeSchema
from models.repo_models.base_repo_model import BaseRepoModel
from hyperlocal_platform.core.decorators.db_session_handler_dec import start_db_transaction
from core.decorators.error_handler_dec import catch_errors
from hyperlocal_platform.core.models.req_res_models import SuccessResponseTypDict,ErrorResponseTypDict,BaseResponseTypDict
from fastapi.exceptions import HTTPException
from hyperlocal_platform.core.enums.timezone_enum import TimeZoneEnum
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Dict

def _map_employee(row) -> Optional[dict]:
    if not row:
        return None
    d = dict(row)
    return d

class EmployeeRepo(BaseRepoModel):
    def __init__(self, session:AsyncSession):
        super().__init__(session)
        # Select columns from both Employees and Users
        self.select_cols = (
            Employees.id,
            Employees.ui_id,
            Employees.user_id,
            Employees.name,
            Employees.shop_id,
            Employees.role,
            Employees.department,
            Employees.accepted,
            Employees.joined_date,
            Employees.created_at,
            Employees.updated_at,
            Employees.additional_infos,
            Employees.added_by
        )

    @start_db_transaction
    async def get_next_sequence(self, shop_id: str, start_from: int) -> int:
        from sqlalchemy import text
        seq_name = f"seq_employee_{shop_id.replace('-', '_').lower()}"
        await self.session.execute(text(f"CREATE SEQUENCE IF NOT EXISTS {seq_name} START WITH {start_from}"))
        res = await self.session.execute(text(f"SELECT nextval('{seq_name}')"))
        return res.scalar_one()

    @start_db_transaction
    async def create(self, data:CreateEmployeeDbSchema)-> dict:
        stmt=(
            insert(Employees)
            .values(**data.model_dump())
            .returning(
                Employees.id,
                Employees.ui_id,
                Employees.user_id,
                Employees.name,
                Employees.shop_id,
                Employees.role,
                Employees.department,
                Employees.accepted,
                Employees.joined_date,
                Employees.created_at,
                Employees.updated_at,
                Employees.additional_infos,
                Employees.added_by
            )
        )
        res=(await self.session.execute(stmt)).mappings().one_or_none()
        
        # Join with Users table to get the full detail
        if res:
            stmt_join = (
                select(*self.select_cols)
                .where(Employees.id == res.get("id"))
            )
            joined_res = (await self.session.execute(stmt_join)).mappings().one_or_none()
            return _map_employee(joined_res)
        return None
    

    @start_db_transaction
    async def update(self, data:UpdateEmployeeDbSchema)-> dict | None:
        values = data.model_dump(exclude=['id','shop_id'], exclude_unset=True, exclude_none=True)
        employee_toupdate=(
            update(Employees)
            .where(
                Employees.id==data.id,
                Employees.shop_id==data.shop_id
            )
            .values(**values)
        ).returning(
            Employees.id,
            Employees.ui_id,
            Employees.user_id,
            Employees.name,
            Employees.shop_id,
            Employees.role,
            Employees.department,
            Employees.accepted,
            Employees.joined_date,
            Employees.created_at,
            Employees.updated_at,
            Employees.additional_infos,
            Employees.added_by
        )

        res=(await self.session.execute(employee_toupdate)).mappings().one_or_none()
        if res:
            stmt_join = (
                select(*self.select_cols)
                .where(Employees.id == res.get("id"))
            )
            joined_res = (await self.session.execute(stmt_join)).mappings().one_or_none()
            return _map_employee(joined_res)
        return None
    

    @start_db_transaction
    async def delete(self,data:DeleteEmployeeSchema)-> dict | None:
        # Get old data first to return it
        stmt_join = (
            select(*self.select_cols)
            .where(Employees.id == data.id, Employees.shop_id == data.shop_id)
        )
        joined_res = (await self.session.execute(stmt_join)).mappings().one_or_none()

        employee_todel=(
            delete(Employees)
            .where(
                Employees.id==data.id,
                Employees.shop_id==data.shop_id
            )
        )
        await self.session.execute(employee_todel)
        return _map_employee(joined_res)
    

    async def get(self,data:GetAllEmployeesSchema)-> List[dict] | None:
        from datetime import datetime
        cursor=(data.offset-1)*data.limit

        conds = []
        if getattr(data, 'query', None):
            search_term=f"%{data.query}%"
            conds.append(
                or_(
                    Employees.id.ilike(search_term),
                    Employees.ui_id.ilike(search_term),
                    Employees.name.ilike(search_term)
                )
            )
        if getattr(data, 'role', None):
            conds.append(Employees.role.ilike(f"%{data.role}%"))
        if getattr(data, 'department', None):
            conds.append(Employees.department.ilike(f"%{data.department}%"))
        if getattr(data, 'from_date', None):
            try:
                from_dt = datetime.strptime(data.from_date, "%Y-%m-%d")
                conds.append(Employees.created_at >= from_dt)
            except Exception:
                pass
        if getattr(data, 'to_date', None):
            try:
                to_date_str = data.to_date
                if len(to_date_str) <= 10:
                    to_date_str += ' 23:59:59'
                to_dt = datetime.strptime(to_date_str, "%Y-%m-%d %H:%M:%S")
                conds.append(Employees.created_at <= to_dt)
            except Exception:
                pass

        employee_stmt=(
            select(*self.select_cols, created_at)
            .where(and_(*conds))
            .limit(limit=data.limit)
            .offset(offset=cursor)
        )

        employees=(await self.session.execute(employee_stmt)).mappings().all()
        return [_map_employee(e) for e in employees]
    

    async def getby_id(self,data:GetEmployeeByIdSchema)-> dict | None:
        created_at=func.date(func.timezone(data.timezone.value,Employees.created_at))

        employee_stmt=(
            select(*self.select_cols, created_at)
            .where(
                Employees.shop_id==data.shop_id,
                Employees.id==data.id,
            )
        )

        employee=(await self.session.execute(employee_stmt)).mappings().one_or_none()
        return _map_employee(employee)
    

    async def getby_shopid(self,data:GetEmployeeByShopIdSchema)-> List[dict] | list:
        from datetime import datetime
        cursor=(data.offset-1)*data.limit

        conds = [Employees.shop_id==data.shop_id]
        if getattr(data, 'query', None):
            search_term=f"%{data.query}%"
            conds.append(
                or_(
                    Employees.id.ilike(search_term),
                    Employees.ui_id.ilike(search_term),
                    Employees.name.ilike(search_term)
                )
            )
        if getattr(data, 'role', None):
            conds.append(Employees.role.ilike(f"%{data.role}%"))
        if getattr(data, 'department', None):
            conds.append(Employees.department.ilike(f"%{data.department}%"))
        if getattr(data, 'from_date', None):
            try:
                from_dt = datetime.strptime(data.from_date, "%Y-%m-%d")
                conds.append(Employees.created_at >= from_dt)
            except Exception:
                pass
        if getattr(data, 'to_date', None):
            try:
                to_date_str = data.to_date
                if len(to_date_str) <= 10:
                    to_date_str += ' 23:59:59'
                to_dt = datetime.strptime(to_date_str, "%Y-%m-%d %H:%M:%S")
                conds.append(Employees.created_at <= to_dt)
            except Exception:
                pass

        employee_stmt=(
            select(*self.select_cols, created_at)
            .where(and_(*conds))
            .limit(limit=data.limit)
            .offset(offset=cursor)
        )

        employees=(await self.session.execute(employee_stmt)).mappings().all()
        return [_map_employee(e) for e in employees]
    
    async def verify_employee(self,data:VerifyEmployeeSchema) -> dict | None:
        conditions = []
        if data.employee_id:
            conditions.append(Employees.id == data.employee_id)
            
        if not conditions:
            return {"id":'','exists':False}

        stmt=(
            select(Employees.id)
            .where(
                Employees.shop_id==data.shop_id,
                or_(*conditions)
            )
        )

        result=(await self.session.execute(stmt)).scalar_one_or_none()

        if result:
            return {"id":result,'exists':True}
        
        return {"id":'','exists':False}
    

    async def search(self, query:str, limit:int):
        """This is just a wrapper for ABC(Abstract Class) of BaseRepo"""
        ...

    async def get_overall_values(self, data: GetAllEmployeesSchema | GetEmployeeByShopIdSchema) -> dict:
        search_term = f"%{data.query}%" if hasattr(data, 'query') else "%%"
        
        stmt = (
            select(func.count(Employees.id).label("total_employees"))
        )
        
        if hasattr(data, 'shop_id') and data.shop_id:
            stmt = stmt.where(Employees.shop_id == data.shop_id)
            
        if hasattr(data, 'query') and data.query:
            created_at = func.date(func.timezone(data.timezone.value, Employees.created_at))
            stmt = stmt.where(
                or_(
                    Employees.id.ilike(search_term),
                    Employees.ui_id.ilike(search_term),
                    func.cast(created_at, String).ilike(search_term)
                )
            )

        res = (await self.session.execute(stmt)).mappings().one_or_none()
        
        return {
            "total_employees": res["total_employees"] or 0
        } if res else {
            "total_employees": 0
        }

    @start_db_transaction
    async def accept_employee(self, employee_id: str, shop_id: str) -> bool:
        stmt = (
            update(Employees)
            .where(Employees.id == employee_id, Employees.shop_id == shop_id)
            .values(accepted=True)
        )
        res = await self.session.execute(stmt)
        return res.rowcount > 0

    @start_db_transaction
    async def is_employee_exists(self, employee_account_id: str, shop_id: str) -> Optional[dict]:
        stmt = (
            select(*self.select_cols)
            .where(
                Employees.user_id == employee_account_id,
                Employees.shop_id == shop_id
            )
        )
        res = (await self.session.execute(stmt)).mappings().one_or_none()
        return _map_employee(res)
