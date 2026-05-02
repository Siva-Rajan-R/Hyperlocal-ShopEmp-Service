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
from typing import Optional,List


class EmployeeRepo(BaseRepoModel):
    def __init__(self, session:AsyncSession):
        super().__init__(session)
        self.employee_cols=(
            Employees.id,
            Employees.sequence_id,
            Employees.shop_id,
            Employees.account_id,
            Employees.datas,
            Employees.name,
            Employees.mobile_number,
            Employees.email,
            Employees.department,
            Employees.joined_date,
            Employees.role,
            Employees.created_at,
            Employees.updated_at,
            Employees.ui_id
        )

    async def is_employee_exists(self,employee_account_id:str,mobile_number:Optional[str]=None,shop_id:Optional[str]=None):
        """This repo method will give the shop existence based on the 
            employee-id, account-id,mobile-number and also you can be able to check with shop-id
        """
        or_conditions=[
            Employees.id==employee_account_id,
            Employees.account_id==employee_account_id
        ]

        if mobile_number:
            or_conditions.append(Employees.datas['mobile_number'].astext==mobile_number)

        and_conditions=[or_(*or_conditions)]

        if shop_id:
            and_conditions.append(Employees.shop_id==shop_id)

        return (await self.session.execute(
            select(*self.employee_cols)
            .where(and_(*and_conditions))
            .limit(1)
        )).mappings().one_or_none()
    


    @start_db_transaction
    async def create(self, data:CreateEmployeeDbSchema)-> dict:
        stmt=(
            insert(
                Employees
            )
            .values(
                **data.model_dump()
            )
            .returning(*self.employee_cols)
        )
        res=(await self.session.execute(stmt)).mappings().one_or_none()
        return res
    

    @start_db_transaction
    async def update(self, data:UpdateEmployeeDbSchema)-> dict | None:
        employee_toupdate=(
            update(Employees)
            .where(
                Employees.id==data.id,
                Employees.shop_id==data.shop_id
            )
            .values(**data.model_dump(exclude=['id','account_id','shop_id'],exclude_unset=True,exclude_none=True))
        ).returning(
            *self.employee_cols
        )

        is_updated=(await self.session.execute(employee_toupdate)).mappings().one_or_none()

        return is_updated
    

    @start_db_transaction
    async def delete(self,data:DeleteEmployeeSchema)-> dict | None:
        employee_todel=(
            delete(Employees)
            .where(
                Employees.id==data.employee_id,
                Employees.shop_id==data.shop_id
            )
        ).returning(
            *self.employee_cols
        )

        is_deleted=(await self.session.execute(employee_todel)).mappings().one_or_none()

        return is_deleted
    

    async def get(self,data:GetAllEmployeesSchema)-> List[dict] | None:
        """This repo method for internal use only not to expose it on public !"""
        search_term=f"%{data.query}%"
        created_at=func.date(func.timezone(data.timezone.value,Employees.created_at))
        cursor=(data.offset-1)*data.limit

        employee_stmt=(
            select(
                *self.employee_cols,
                created_at,
            )
            .where(
                and_(
                    or_(
                        Employees.id.ilike(search_term),
                        Employees.account_id.ilike(search_term),
                        func.cast(created_at,String).ilike(search_term)
                    ),
                    Employees.sequence_id>cursor
                )
                
            )
            .limit(limit=data.limit)
            .offset(offset=cursor)
        )

        employees=(await self.session.execute(employee_stmt)).mappings().all()

        return employees
    

    async def getby_id(self,data:GetEmployeeByIdSchema)-> dict | None:
        """This repo method for internal use only not to expose it on public !"""
        created_at=func.date(func.timezone(data.timezone.value,Employees.created_at))

        employee_stmt=(
            select(
                *self.employee_cols,
                created_at,
            )
            .where(
                Employees.id==data.employee_id,
            )
        )

        employee=(await self.session.execute(employee_stmt)).mappings().one_or_none()

        return employee
    

    async def getby_shopid(self,data:GetEmployeeByShopIdSchema)-> List[dict] | list:
        """This repo method for internal use only not to expose it on public !"""
        search_term=f"%{data.query}%"
        created_at=func.date(func.timezone(data.timezone.value,Employees.created_at))
        cursor=(data.offset-1)*data.limit

        employee_stmt=(
            select(
                *self.employee_cols,
                created_at,
            )
            .where(
                and_(
                    Employees.shop_id==data.shop_id,
                    or_(
                        Employees.id.ilike(search_term),
                        Employees.account_id.ilike(search_term),
                        func.cast(created_at,String).ilike(search_term)
                    ),
                    Employees.sequence_id>cursor
                )
                
            )
            .limit(limit=data.limit)
            .offset(offset=cursor)
        )

        employees=(await self.session.execute(employee_stmt)).mappings().all()

        return employees
    
    async def verify_employee(self,data:VerifyEmployeeSchema) -> dict | None:
        stmt=(
            select(
                Employees.id
            )
            .where(
                Employees.shop_id==data.shop_id,
                or_(
                    Employees.id==data.employee_id,
                    Employees.mobile_number==data.mobile_number,
                    Employees.email==data.email
                )
            )
        )

        result=(await self.session.execute(stmt)).scalar_one_or_none()

        if result:
            return {"id":result,'exists':True}
        
        return {"id":'','exists':False}
    

    async def search(self, query:str, limit:int):
        """This is just a wrapper for ABC(Abstract Class) of BaseRepo"""
        ...

