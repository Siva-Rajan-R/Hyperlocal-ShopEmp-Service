from fastapi import APIRouter, Depends, Query,Query
from fastapi.responses import RedirectResponse
from infras.primary_db.main import get_pg_async_session, AsyncSession
from api.handlers.auth import HandleAuthRequest
from typing import Annotated
from integrations.debuth_service import get_loggedin_user,get_login_urls
from infras.primary_db.services.user_service import UserService
from icecream import ic

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
    return await HandleAuthRequest(session=session).verify_employee(token=token)


@router.get('/init')
async def get_login_url():
    urls=await get_login_urls()
    ic(urls)
    signin_url=urls['signin_url']
    signup_url=urls['signup_url']
    return signin_url


@router.get("/redirect")
async def create_user(session: PG_ASYNC_SESSION,token_id:str=Query(...)):
    res = await get_loggedin_user(token_id=token_id)
    ic(res)
    user_email=res['email']
    user_name=res.get("name") if res.get("name") else user_email.split("@")[0] 
    mobile_number=None
    await UserService(session=session).get_or_create_user(
        name=user_name,
        email=user_email,
        mobile_number=mobile_number
    )

    return RedirectResponse(
        url=f"http://localhost:5173/dashboard",
        status_code=302
    )


