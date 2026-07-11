from fastapi import APIRouter,Depends,Query,Header,File,UploadFile,Form
from infras.primary_db.main import get_pg_async_session,AsyncSession
from ...handlers.shop import (
    HandleShopRequest,CreateShopSchema,UpdateShopSchema,DeleteShopSchema,TimeZoneEnum,Optional,
    GetAllShopsSchema,GetShopByUserIdSchema,GetShopByIdSchema,
    CreateOperatingHoursSchema, UpdateOperatingHoursSchema,
    CreateDeliverySchema, UpdateDeliverySchema,
    CreateAnnouncementSchema, UpdateAnnouncementSchema
)
from core.permissions.role_checker import require_permission
from typing import Annotated,List,Literal
from icecream import ic
from pydantic import BaseModel
from integrations.utility_service import upload_assets,delete_assets

class UploadImagesSchema(BaseModel):
    user_id:str
    shop_id:str
    image_type:Literal['logo','banner']

    @classmethod
    def as_form(
        cls,
        shop_id:str=Form(...),
        image_type:Literal['logo','banner']=Form(...),
        user_id:str=Form(...)
    ):
        return cls(
            shop_id=shop_id,
            image_type=image_type,
            user_id=user_id
        )


class DeleteImagesSchema(BaseModel):
    user_id:str
    shop_id:str
    urls:List[str]
    image_type:Literal['logo','banner']

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


@router.post('/upload/images')
async def upload_images(session:PG_ASYNC_SESSION,data:Annotated[UploadImagesSchema,Depends(UploadImagesSchema.as_form)],files:List[UploadFile]=File(...)):
    res=await upload_assets(files=files)
    ic(res,data.shop_id,data.image_type)
    
    url = res.get("data", [None])[0] if isinstance(res, dict) else None
    ic(url)
    return await HandleShopRequest(session=session).update(
        user_id=data.user_id,
        data=UpdateShopSchema(
            id=data.shop_id,
            banner_url=url if data.image_type=="banner" else None,
            logo_url=url if data.image_type=="logo" else None
        )
    )


@router.delete('/upload/images')
async def delete_images(session:PG_ASYNC_SESSION,data:DeleteImagesSchema):
    deleted=await delete_assets(urls=data.urls)
    ic(deleted,data.urls,data.shop_id,data.ima)
    return await HandleShopRequest(session=session).update(
        user_id=data.user_id,
        data=UpdateShopSchema(
            id=data.shop_id,
            banner_url="" if data.image_type=="banner" else None,
            logo_url="" if data.image_type=="logo" else None
        )
    )

# Read methods
@router.get('/my-shops')
async def get_my_shops(
    session: PG_ASYNC_SESSION,
    session_id: str = Query(None),
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID")
):
    ic("Received get_my_shops request", session_id, x_session_id)
    sess_id = session_id or x_session_id
    if not sess_id:
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Session ID required")
    
    import json
    import os
    import redis.asyncio as aioredis
    from fastapi import HTTPException
    
    redis_url = os.getenv("PLATFORM_REDIS_URL", "redis://localhost:6379")
    redis_client = aioredis.Redis.from_url(redis_url, decode_responses=True)
    
    session_data = await redis_client.get(f"SESSION:{sess_id}")
    if not session_data:
        raise HTTPException(status_code=401, detail="Session expired or invalid")
    
    sess_info = json.loads(session_data)
    user_id = sess_info.get("user_id")
    
    data = GetShopByUserIdSchema(user_id=user_id)
    return await HandleShopRequest(session=session).getby_userid(data=data)

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


# --- Operating Hours Routes ---
@router.post('/{shop_id}/operating-hours')
async def add_operating_hours(
    shop_id: str,
    data: CreateOperatingHoursSchema,
    session: PG_ASYNC_SESSION,
    auth_data: Annotated[dict, Depends(require_permission("update_shop"))]
):
    return await HandleShopRequest(session=session).add_operating_hours(shop_id=shop_id, data=data)

@router.get('/{shop_id}/operating-hours')
async def get_operating_hours(
    shop_id: str,
    session: PG_ASYNC_SESSION
):
    return await HandleShopRequest(session=session).get_operating_hours(shop_id=shop_id)

@router.put('/operating-hours/{hours_id}')
async def update_operating_hours(
    hours_id: int,
    data: UpdateOperatingHoursSchema,
    session: PG_ASYNC_SESSION,
    auth_data: Annotated[dict, Depends(require_permission("update_shop"))]
):
    return await HandleShopRequest(session=session).update_operating_hours(hours_id=hours_id, data=data)

@router.delete('/operating-hours/{hours_id}')
async def delete_operating_hours(
    hours_id: int,
    session: PG_ASYNC_SESSION,
    auth_data: Annotated[dict, Depends(require_permission("update_shop"))]
):
    return await HandleShopRequest(session=session).delete_operating_hours(hours_id=hours_id)


# --- Delivery Routes ---
@router.post('/{shop_id}/delivery')
async def add_delivery_options(
    shop_id: str,
    data: CreateDeliverySchema,
    session: PG_ASYNC_SESSION,
    auth_data: Annotated[dict, Depends(require_permission("update_shop"))]
):
    return await HandleShopRequest(session=session).add_delivery_options(shop_id=shop_id, data=data)

@router.get('/{shop_id}/delivery')
async def get_delivery_options(
    shop_id: str,
    session: PG_ASYNC_SESSION
):
    return await HandleShopRequest(session=session).get_delivery_options(shop_id=shop_id)

@router.put('/delivery/{delivery_id}')
async def update_delivery_options(
    delivery_id: int,
    data: UpdateDeliverySchema,
    session: PG_ASYNC_SESSION,
    auth_data: Annotated[dict, Depends(require_permission("update_shop"))]
):
    return await HandleShopRequest(session=session).update_delivery_options(delivery_id=delivery_id, data=data)

@router.delete('/delivery/{delivery_id}')
async def delete_delivery_options(
    delivery_id: int,
    session: PG_ASYNC_SESSION,
    auth_data: Annotated[dict, Depends(require_permission("update_shop"))]
):
    return await HandleShopRequest(session=session).delete_delivery_options(delivery_id=delivery_id)


# --- Announcements Routes ---
@router.post('/{shop_id}/announcements')
async def add_announcement(
    shop_id: str,
    data: CreateAnnouncementSchema,
    session: PG_ASYNC_SESSION,
    auth_data: Annotated[dict, Depends(require_permission("update_shop"))]
):
    return await HandleShopRequest(session=session).add_announcement(shop_id=shop_id, data=data)

@router.get('/{shop_id}/announcements')
async def get_announcements(
    shop_id: str,
    session: PG_ASYNC_SESSION
):
    return await HandleShopRequest(session=session).get_announcements(shop_id=shop_id)

@router.put('/announcements/{announcement_id}')
async def update_announcement(
    announcement_id: int,
    data: UpdateAnnouncementSchema,
    session: PG_ASYNC_SESSION,
    auth_data: Annotated[dict, Depends(require_permission("update_shop"))]
):
    return await HandleShopRequest(session=session).update_announcement(announcement_id=announcement_id, data=data)

@router.delete('/announcements/{announcement_id}')
async def delete_announcement(
    announcement_id: int,
    session: PG_ASYNC_SESSION,
    auth_data: Annotated[dict, Depends(require_permission("update_shop"))]
):
    return await HandleShopRequest(session=session).delete_announcement(announcement_id=announcement_id)