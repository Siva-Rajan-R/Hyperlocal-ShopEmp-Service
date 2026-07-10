from fastapi import APIRouter, Depends, Query,Query
from fastapi.responses import RedirectResponse
from infras.primary_db.main import get_pg_async_session, AsyncSession
from api.handlers.auth import HandleAuthRequest
from typing import Annotated
from integrations.debuth_service import get_loggedin_user,get_login_urls
from infras.primary_db.services.user_service import UserService
from icecream import ic
import os
from dotenv import load_dotenv
load_dotenv()

router = APIRouter(
    tags=['Auth'],
    prefix="/auth"
)

PG_ASYNC_SESSION = Annotated[AsyncSession, Depends(get_pg_async_session)]

@router.get('/user-check')
async def user_check(
    session: PG_ASYNC_SESSION,
    email: str = Query(...),
    name: str = Query("Anonymous"),
    mobile_number: str = Query("")
):
    return await HandleAuthRequest(session=session).check_user(email=email, name=name, mobile_number=mobile_number)

@router.get('/shop-check')
async def shop_check(
    session: PG_ASYNC_SESSION,
    user_id: str = Query(...)
):
    return await HandleAuthRequest(session=session).check_shop(user_id=user_id)

@router.get('/verify')
async def verify_employee(
    session: PG_ASYNC_SESSION,
    token: str = Query(...)
):
    
    frontend_url = os.getenv("FRONTEND_BASE_URL", "http://localhost:5173")
    try:
        res = await HandleAuthRequest(session=session).verify_employee(token=token)
        payload = res.get("data", {}) if isinstance(res, dict) else {}
        return RedirectResponse(
            url=f"{frontend_url}/employee/verify?status=success&employee_id={payload.get('employee_id', '')}&shop_id={payload.get('shop_id', '')}",
            status_code=302
        )
    except Exception:
        return RedirectResponse(url=f"{frontend_url}/employee/verify?status=failed", status_code=302)

@router.get('/init')
async def get_login_url():
    urls=await get_login_urls()
    ic(urls)
    signin_url=urls['signin_url']
    signup_url=urls['signup_url']
    return signin_url


@router.get("/redirect")
async def create_user(session: PG_ASYNC_SESSION, token_id: str = Query(...)):
    res = await get_loggedin_user(token_id=token_id)
    ic(res)
    user_email = res['email']
    user_name = res.get("name") if res.get("name") else user_email.split("@")[0] 
    mobile_number = None
    user_data = await UserService(session=session).get_or_create_user(
        name=user_name,
        email=user_email,
        mobile_number=mobile_number
    )

    # 1. Generate session ID
    from hyperlocal_platform.core.utils.uuid_generator import generate_uuid
    session_id = generate_uuid()

    # 2. Save session info in Redis (expires in 15 minutes)
    import json
    import os
    import redis.asyncio as aioredis
    redis_url = os.getenv("PLATFORM_REDIS_URL", "redis://localhost:6379")
    redis_client = aioredis.Redis.from_url(redis_url, decode_responses=True)
    
    session_info = {
        "user_id": user_data["id"],
        "role": "OWNER"  # Default role initially
    }
    await redis_client.set(f"SESSION:{session_id}", json.dumps(session_info), ex=900)

    # 3. Redirect to dashboard sending session_id to frontend
    return RedirectResponse(
        url=f"http://localhost:5173/dashboard?session_id={session_id}&user_id={user_data['id']}&email={user_email}&name={user_name}",
        status_code=302
    )

from pydantic import BaseModel
from fastapi import HTTPException

class TokenCreateRequest(BaseModel):
    session_id: str
    shop_id: str

class TokenRefreshRequest(BaseModel):
    refresh_token: str

@router.post('/token/create')
async def create_token(data: TokenCreateRequest, session: PG_ASYNC_SESSION):
    import json
    import os
    import redis.asyncio as aioredis
    from core.permissions.role_checker import get_user_role
    from core.utils.auth_helper import create_access_token, create_refresh_token
    from infras.primary_db.services.shop_service import ShopService
    from schemas.v1.request_schemas.shop_schemas import GetShopByIdSchema

    redis_url = os.getenv("PLATFORM_REDIS_URL", "redis://localhost:6379")
    redis_client = aioredis.Redis.from_url(redis_url, decode_responses=True)

    # 1. Verify session_id exists in Redis
    session_data = await redis_client.get(f"SESSION:{data.session_id}")
    if not session_data:
        raise HTTPException(status_code=401, detail="Session expired or invalid")

    sess_info = json.loads(session_data)
    user_id = sess_info.get("user_id")

    # 2. Get role of user for selected shop
    role = await get_user_role(user_id=user_id, shop_id=data.shop_id, session=session)
    if not role:
        raise HTTPException(status_code=403, detail="Access denied: Not authorized for this shop")
    
    # 3. Check GST registered status of the shop
    shop_service = ShopService(session=session)
    shop = await shop_service.getby_id(GetShopByIdSchema(shop_id=data.shop_id))
    gst_registered = False
    if shop and shop.get("business_infos"):
        bus_infos = shop.get("business_infos")
        if isinstance(bus_infos, str):
            try:
                bus_infos = json.loads(bus_infos)
            except Exception:
                bus_infos = {}
        if isinstance(bus_infos, dict):
            gst_infos = bus_infos.get("gst_infos") or {}
            gst_registered = gst_infos.get("registered", False)
    
    # 4. Generate JWT tokens
    access_token = create_access_token(user_id=user_id, role=role, shop_id=data.shop_id, gst_registered=gst_registered)
    refresh_token = create_refresh_token(user_id=user_id, role=role, shop_id=data.shop_id, gst_registered=gst_registered)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token
    }

@router.post('/shop-checkin')
async def shop_checkin(data: TokenCreateRequest, session: PG_ASYNC_SESSION):
    # Call create_token to perform the exact check-in verification and token return
    return await create_token(data=data, session=session)

@router.post('/token/refresh')
async def refresh_token(data: TokenRefreshRequest):
    from core.utils.auth_helper import decode_refresh_token, create_access_token

    # 1. Decode and verify refresh token
    payload = decode_refresh_token(data.refresh_token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    # 2. Generate new access token
    new_access_token = create_access_token(
        user_id=payload.get("user_id"),
        role=payload.get("role"),
        shop_id=payload.get("shop_id"),
        gst_registered=payload.get("gst_registered", False)
    )

    return {
        "access_token": new_access_token
    }




