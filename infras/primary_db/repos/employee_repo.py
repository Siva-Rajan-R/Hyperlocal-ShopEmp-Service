from ..models.employee_model import Employees
from sqlalchemy import select,update,delete,or_,and_,func,String
from schemas.v1.db_schemas.employee_schema import CreateEmployeeDbSchema,UpdateEmployeeDbSchema
from models.repo_models.base_repo_model import BaseRepoModel
from hyperlocal_platform.core.decorators.db_session_handler_dec import start_db_transaction
from core.decorators.error_handler_dec import catch_errors
from hyperlocal_platform.core.models.req_res_models import SuccessResponseTypDict,ErrorResponseTypDict,BaseResponseTypDict
from fastapi.exceptions import HTTPException
from hyperlocal_platform.core.enums.timezone_enum import TimeZoneEnum
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional


class EmployeeRepo(BaseRepoModel):
    def __init__(self, session:AsyncSession):
        super().__init__(session)
        self.employee_cols=(
            Employees.id,
            Employees.shop_id,
            Employees.account_id,
            Employees.datas
        )

    @catch_errors
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
    

    @catch_errors
    @start_db_transaction
    async def create(self, data:CreateEmployeeDbSchema):
        self.session.add(Employees(**data.model_dump(mode="json")))
        return data
    

    @catch_errors
    @start_db_transaction
    async def update(self, data:UpdateEmployeeDbSchema):
        employee_toupdate=(
            update(Employees)
            .where(
                Employees.account_id==data.account_id,
                Employees.id==data.id,
                Employees.shop_id==data.shop_id
            )
            .values(**data.model_dump(mode="json",exclude=['id','account_id','shop_id'],exclude_unset=True))
        ).returning(Employees.id)

        is_updated=(await self.session.execute(employee_toupdate)).scalar_one_or_none()

        return is_updated
    

    @catch_errors
    @start_db_transaction
    async def delete(self,employee_id:str,shop_id:str,added_acc_id:str):
        employee_todel=(
            delete(Employees)
            .where(
                Employees.id==employee_id,
                Employees.shop_id==shop_id,
                Employees.added_by==added_acc_id
            )
        ).returning(Employees.id)

        is_deleted=(await self.session.execute(employee_todel)).scalar_one_or_none()

        return is_deleted
    

    @catch_errors
    async def get(self,query:str,limit:int,offset:int,timezone:TimeZoneEnum):
        """This repo method for internal use only not to expose it on public !"""
        search_term=f"%{query}%"
        created_at=func.date(func.timezone(timezone.value,Employees.created_at))
        cursor=(offset-1)*limit

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
            .limit(limit=limit)
            .order_by(created_at) 
        )

        employees=(await self.session.execute(employee_stmt)).mappings().all()

        return employees
    

    @catch_errors
    async def getby_id(self,employee_id:str,timezone:TimeZoneEnum):
        """This repo method for internal use only not to expose it on public !"""
        created_at=func.date(func.timezone(timezone.value,Employees.created_at))

        employee_stmt=(
            select(
                *self.employee_cols,
                created_at,
            )
            .where(
                Employees.id==employee_id,
            )
        )

        employee=(await self.session.execute(employee_stmt)).mappings().one_or_none()

        return employee
    

    @catch_errors
    async def getby_shopid(self,shop_id:str,timezone:TimeZoneEnum):
        """This repo method for internal use only not to expose it on public !"""
        created_at=func.date(func.timezone(timezone.value,Employees.created_at))
        shop_stmt=(
            select(
                *self.employee_cols,
                created_at

            )
            .where(
                Employees.shop_id==shop_id
            )
        )

        shops=(await self.session.execute(shop_stmt)).mappings().all()

        return shops
    

    @catch_errors
    async def search(self, query:str, limit:int):
        """This is just a wrapper for ABC(Abstract Class) of BaseRepo"""
        ...

