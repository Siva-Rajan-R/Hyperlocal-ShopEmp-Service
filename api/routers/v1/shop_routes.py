from fastapi import APIRouter,Depends,Query
from infras.primary_db.main import get_pg_async_session,AsyncSession
from ...handlers.shop import HandleShopRequest,CreateShopSchema,UpdateShopSchema,TimeZoneEnum,Optional
from typing import Annotated


router=APIRouter(
    tags=['Shop CRUD'],
    prefix="/shops"
)

PG_ASYNC_SESSION=Annotated[AsyncSession,Depends(get_pg_async_session)]

# Write methods
@router.post('')
async def create(data:CreateShopSchema,session:PG_ASYNC_SESSION):
    return await HandleShopRequest(session=session).create(data=data,account_id="")

@router.put('')
async def update(data:UpdateShopSchema,session:PG_ASYNC_SESSION):
    return await HandleShopRequest(session=session).update(data=data,account_id="")

@router.delete('/{shop_id}')
async def delete(shop_id:str,session:PG_ASYNC_SESSION):
    return await HandleShopRequest(session=session).delete(shop_id=shop_id,account_id="")


# Read methods
@router.get('/by/account/{account_id}')
async def get_by_accountid(session:PG_ASYNC_SESSION,account_id:str,timezone:Optional[TimeZoneEnum]=Query(TimeZoneEnum.Asia_Kolkata)):
    # need to get the account_id from header not from the route
    return await HandleShopRequest(session=session).getby_accountid(account_id="",timezone=timezone)

@router.get('/by/{shop_id}')
async def get_by_shopid(session:PG_ASYNC_SESSION,shop_id:str,timezone:Optional[TimeZoneEnum]=Query(TimeZoneEnum.Asia_Kolkata)):
    return await HandleShopRequest(session=session).getby_id(shop_id=shop_id,timezone=timezone)

@router.get('/search')
async def search(session:PG_ASYNC_SESSION,q:str=Query(...),limit:Optional[int]=Query(5)):
    return await HandleShopRequest(session=session).search(query=q,limit=limit)

@router.get('')
async def get_all(session:PG_ASYNC_SESSION,timezone:Optional[TimeZoneEnum]=Query(TimeZoneEnum.Asia_Kolkata),q:Optional[str]=Query(""),limit:Optional[int]=Query(10),offset:int=Query(1)):
    return await HandleShopRequest(session=session).get(timezone=timezone,query=q,limit=limit,offset=offset)