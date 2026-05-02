from fastapi import APIRouter,Depends,Query
from infras.primary_db.main import get_pg_async_session,AsyncSession
from ...handlers.shop import HandleShopRequest,CreateShopSchema,UpdateShopSchema,DeleteShopSchema,TimeZoneEnum,Optional,GetAllShopsSchema,GetShopByAccountIdSchema,GetShopByIdSchema
from typing import Annotated


router=APIRouter(
    tags=['Shop CRUD'],
    prefix="/shops"
)

PG_ASYNC_SESSION=Annotated[AsyncSession,Depends(get_pg_async_session)]
ACCOUNT_ID=""
# Write methods
@router.post('')
async def create(data:CreateShopSchema,session:PG_ASYNC_SESSION):
    return await HandleShopRequest(session=session).create(data=data,account_id=ACCOUNT_ID)

@router.put('')
async def update(data:UpdateShopSchema,session:PG_ASYNC_SESSION):
    return await HandleShopRequest(session=session).update(data=data,account_id=ACCOUNT_ID)

@router.delete('/{shop_id}')
async def delete(session:PG_ASYNC_SESSION,data:DeleteShopSchema=Depends()):
    return await HandleShopRequest(session=session).delete(data=data,account_id=ACCOUNT_ID)


# Read methods
@router.get('/by/account/{account_id}')
async def get_by_accountid(session:PG_ASYNC_SESSION,data:GetShopByAccountIdSchema=Depends()):
    # need to get the account_id from header not from the route
    return await HandleShopRequest(session=session).getby_accountid(data=data)

@router.get('/by/{shop_id}')
async def get_byid(session:PG_ASYNC_SESSION,data:GetShopByIdSchema=Depends()):
    return await HandleShopRequest(session=session).getby_id(data=data)


@router.get('')
async def get_all(session:PG_ASYNC_SESSION,data:GetAllShopsSchema=Depends()):
    return await HandleShopRequest(session=session).get(data=data)