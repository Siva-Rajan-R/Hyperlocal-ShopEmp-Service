from fastapi import APIRouter,Depends,Query
from infras.primary_db.main import get_pg_async_session,AsyncSession
from typing import Annotated
from ...handlers.employee import HandleEmployeeRequest,CreateEmployeeSchema,UpdateEmployeeSchema,DeleteEmployeeSchema,GetAllEmployeesSchema,GetEmployeeByIdSchema,GetEmployeeByShopIdSchema,VerifyEmployeeSchema
from infras.read_db.models.employee_model import ReadDbEmployeeReadModel

from typing import List,Optional


router=APIRouter(
    tags=['Employee CRUD'],
    prefix="/employees"
)

PG_ASYNC_SESSION=Annotated[AsyncSession,Depends(get_pg_async_session)]

# Write methods
@router.post('')
async def create(data:CreateEmployeeSchema,session:PG_ASYNC_SESSION):
    return await HandleEmployeeRequest(session=session).create(data=data,account_id="")

@router.put('')
async def update(data:UpdateEmployeeSchema,session:PG_ASYNC_SESSION):
    return await HandleEmployeeRequest(session=session).update(data=data)


@router.delete('/{shop_id}/{employee_id}')
async def delete(session:PG_ASYNC_SESSION,data:DeleteEmployeeSchema=Depends()):
    return await HandleEmployeeRequest(session=session).delete(data=data)

# Read methods
@router.get('/by/shop/{shop_id}')
async def get_by_shopid(session:PG_ASYNC_SESSION,data:GetEmployeeByShopIdSchema=Depends()):
    """This route-method for internal use only not to expose it on public !"""
    return await HandleEmployeeRequest(session=session).getby_shopid(data=data)


@router.get('/by/{employee_id}')
async def get_by_empid(session:PG_ASYNC_SESSION,data:GetEmployeeByIdSchema=Depends()):
    """This route-method for internal use only not to expose it on public !"""
    return await HandleEmployeeRequest(session=session).getby_id(data=data)


@router.get('')
async def get_all(session:PG_ASYNC_SESSION,data:GetAllEmployeesSchema=Depends()):
    """This route-method for internal use only not to expose it on public !"""
    return await HandleEmployeeRequest(session=session).get_all(data=data)