from fastapi import APIRouter,Depends,Query,Header
from infras.primary_db.main import get_pg_async_session,AsyncSession
from ...handlers.shop import HandleShopRequest,CreateShopSchema,UpdateShopSchema,DeleteShopSchema,TimeZoneEnum,Optional,GetAllShopsSchema,GetShopByUserIdSchema,GetShopByIdSchema
from core.permissions.role_checker import require_permission
from typing import Annotated
from icecream import ic

router=APIRouter(
    tags=['Shop CRUD'],
    prefix="/shops"
)

PG_ASYNC_SESSION=Annotated[AsyncSession,Depends(get_pg_async_session)]

# Write methods
@router.post('')
async def create(
    data:CreateShopSchema,
    session:PG_ASYNC_SESSION,
    auth_data: Annotated[str, Depends(require_permission("create_shop"))]
):
    ic("Auth data => ",auth_data)
    # auth_data returns user_id for shop creation
    return await HandleShopRequest(session=session).create(data=data,user_id=auth_data)

@router.put('')
async def update(
    data:UpdateShopSchema,
    session:PG_ASYNC_SESSION,
    auth_data: Annotated[dict, Depends(require_permission("update_shop"))]
):
    return await HandleShopRequest(session=session).update(data=data,user_id=auth_data["user_id"])

@router.delete('/{shop_id}')
async def delete(
    shop_id: str,
    session: PG_ASYNC_SESSION,
    auth_data: Annotated[dict, Depends(require_permission("delete_shop"))]
):
    data = DeleteShopSchema(shop_id=shop_id)
    return await HandleShopRequest(session=session).delete(data=data,user_id=auth_data["user_id"])


# Read methods
@router.get('/by/user/{user_id}')
async def get_by_userid(
    user_id: str,
    session: PG_ASYNC_SESSION,
    data: GetShopByUserIdSchema = Depends()
):
    data.user_id = user_id
    return await HandleShopRequest(session=session).getby_userid(data=data)

@router.get('/by/{shop_id}')
async def get_byid(session:PG_ASYNC_SESSION,data:GetShopByIdSchema=Depends()):
    return await HandleShopRequest(session=session).getby_id(data=data)


@router.get('')
async def get_all(session:PG_ASYNC_SESSION,data:GetAllShopsSchema=Depends()):
    return await HandleShopRequest(session=session).get(data=data)