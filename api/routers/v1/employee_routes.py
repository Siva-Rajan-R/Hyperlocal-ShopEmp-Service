from fastapi import APIRouter,Depends,Query
from infras.primary_db.main import get_pg_async_session,AsyncSession
from typing import Annotated
from ...handlers.employee import HandleEmployeeRequest,CreateEmployeeSchema,UpdateEmployeeSchema,Optional,TimeZoneEnum
from infras.read_db.models.employee_model import ReadDbEmployeeReadModel
from typing import List


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
    return await HandleEmployeeRequest(session=session).update(data=data,account_id="")


@router.delete('/{shop_id}/{employee_id}')
async def delete(shop_id:str,employee_id:str,session:PG_ASYNC_SESSION):
    return await HandleEmployeeRequest(session=session).delete(shop_id=shop_id,employee_id=employee_id,account_id="")

# Read methods
@router.get('/by/shop/{shop_id}')
async def get_by_shopid(session:PG_ASYNC_SESSION,shop_id:str,timezone:Optional[TimeZoneEnum]=Query(TimeZoneEnum.Asia_Kolkata)):
    """This route-method for internal use only not to expose it on public !"""
    return await HandleEmployeeRequest(session=session).getby_shopid(shop_id=shop_id,timezone=timezone)


@router.get('/by/{employee_id}')
async def get_by_empid(session:PG_ASYNC_SESSION,employee_id:str,timezone:Optional[TimeZoneEnum]=Query(TimeZoneEnum.Asia_Kolkata)):
    """This route-method for internal use only not to expose it on public !"""
    return await HandleEmployeeRequest(session=session).getby_id(employee_id=employee_id,timezone=timezone)


@router.get('')
async def get_all(session:PG_ASYNC_SESSION,timezone:Optional[TimeZoneEnum]=Query(TimeZoneEnum.Asia_Kolkata),q:Optional[str]=Query(""),limit:Optional[int]=Query(10),offset:int=Query(1)):
    """This route-method for internal use only not to expose it on public !"""
    return await HandleEmployeeRequest(session=session).get_all(timezone=timezone,q=q,limit=limit,offset=offset)