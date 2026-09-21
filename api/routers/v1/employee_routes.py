from icecream import ic
from fastapi import APIRouter,Depends,Query
from infras.primary_db.main import get_pg_async_session,AsyncSession
from typing import Annotated, List, Optional
from ...handlers.employee import HandleEmployeeRequest,CreateEmployeeSchema,UpdateEmployeeSchema,DeleteEmployeeSchema,GetAllEmployeesSchema,GetEmployeeByIdSchema,GetEmployeeByShopIdSchema,SendVerifyEmployeeSchema,VerifyEmployeeTokenSchema
from core.permissions.role_checker import require_permission
from core.configs.settings_config import SETTINGS
router=APIRouter(
    tags=['Employee CRUD'],
    prefix="/employees"
)

PG_ASYNC_SESSION=Annotated[AsyncSession,Depends(get_pg_async_session)]

# Write methods
@router.post('')
async def create(
    data:CreateEmployeeSchema,
    session:PG_ASYNC_SESSION,
    auth_data: Annotated[dict, Depends(require_permission("create_employee"))]
):
    return await HandleEmployeeRequest(session=session).create(data=data,user_id=auth_data["user_id"])


@router.post('/bulk')
async def create_bulk(
    data:List[CreateEmployeeSchema],
    session:PG_ASYNC_SESSION,
    auth_data: Annotated[dict, Depends(require_permission("create_employee"))]
):
    return await HandleEmployeeRequest(session=session).create_bulk(data=data,user_id=auth_data["user_id"])


@router.put('')
async def update(
    data:UpdateEmployeeSchema,
    session:PG_ASYNC_SESSION,
    auth_data: Annotated[dict, Depends(require_permission("update_employee"))]
):
    return await HandleEmployeeRequest(session=session).update(data=data)

@router.get('/verify/token')
async def verify_token_redirect(session:PG_ASYNC_SESSION, token: str = Query(...)):
    from fastapi.responses import RedirectResponse
    frontend_url = SETTINGS.FRONTEND_BASE_URL or "http://localhost:5173"
    try:
        res = await HandleEmployeeRequest(session=session).verify_token(data=VerifyEmployeeTokenSchema(token=token))
        
        # Handle dict vs Pydantic model for response
        if hasattr(res, "model_dump"):
            res_dict = res.model_dump()
        elif hasattr(res, "dict"):
            res_dict = res.dict()
        elif isinstance(res, dict):
            res_dict = res
        else:
            res_dict = getattr(res, "__dict__", {})

        payload = res_dict.get("data", {})
        if hasattr(payload, "model_dump"):
            payload = payload.model_dump()
        elif hasattr(payload, "dict"):
            payload = payload.dict()
        elif not isinstance(payload, dict):
            payload = getattr(payload, "__dict__", {})

        import urllib.parse
        shop_name_encoded = urllib.parse.quote(payload.get('shop_name', '')) if payload.get('shop_name') else ''
        return RedirectResponse(
            url=f"{frontend_url}/employee/verify?status=success&employee_id={payload.get('employee_id', '')}&shop_id={payload.get('shop_id', '')}&shop_name={shop_name_encoded}",
            status_code=302
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        ic(f"Employee token verification redirect failed: {e}")
        return RedirectResponse(url=f"{frontend_url}/employee/verify?status=failed", status_code=302)

@router.post('/verify/token')
async def verify_token(session:PG_ASYNC_SESSION,data:VerifyEmployeeTokenSchema):
    return await HandleEmployeeRequest(session=session).verify_token(data=data)

@router.post('/verify/resend')
async def resend_verify_token(session:PG_ASYNC_SESSION,data:SendVerifyEmployeeSchema):
    return await HandleEmployeeRequest(session=session).send_verify(data=data)

@router.delete('/{shop_id}/{id}')
async def delete(
    id: str,
    shop_id: str,
    session:PG_ASYNC_SESSION,
    auth_data: Annotated[dict, Depends(require_permission("delete_employee"))]
):
    data = DeleteEmployeeSchema(id=id, shop_id=shop_id)
    return await HandleEmployeeRequest(session=session).delete(data=data)

# Read methods
@router.get('/modules/allowed')
async def get_modules_allowed(
    session: PG_ASYNC_SESSION,
    auth_data: Annotated[dict, Depends(require_permission("read_all"))]
):
    return await HandleEmployeeRequest(session=session).get_allowed_modules(
        user_id=auth_data["user_id"],
        shop_id=auth_data["shop_id"],
        role=auth_data["role"]
    )
@router.get('/by/shop/{shop_id}')
async def get_by_shopid(
    shop_id: str,
    session:PG_ASYNC_SESSION,
    auth_data: Annotated[dict, Depends(require_permission("read_employee"))],
    data:GetEmployeeByShopIdSchema=Depends()
):
    data.shop_id = shop_id
    return await HandleEmployeeRequest(session=session).getby_shopid(data=data)


@router.get('/by/{shop_id}/{id}')
async def get_by_empid(
    id: str,
    shop_id: str,
    session:PG_ASYNC_SESSION,
    auth_data: Annotated[dict, Depends(require_permission("read_employee"))],
    data:GetEmployeeByIdSchema=Depends()
):
    data.id = id
    data.shop_id = shop_id
    return await HandleEmployeeRequest(session=session).getby_id(data=data)


@router.get('')
async def get_all(
    session:PG_ASYNC_SESSION,
    auth_data: Annotated[dict, Depends(require_permission("read_employee"))],
    data:GetAllEmployeesSchema=Depends()
):
    return await HandleEmployeeRequest(session=session).get_all(data=data)

# Internal methods for API Gateway
@router.get('/internal/role/{shop_id}/{user_id}')
async def internal_get_user_role(shop_id: str, user_id: str):
    import time
    from core.permissions.role_checker import get_user_role, _USER_ROLE_CACHE
    cache_key = (user_id, shop_id)
    cached = _USER_ROLE_CACHE.get(cache_key)
    if cached and (time.time() < cached[1]):
        return {"role": cached[0]}

    from infras.primary_db.main import AsyncShopEmployeeLocalSession
    async with AsyncShopEmployeeLocalSession() as session:
        role = await get_user_role(user_id=user_id, shop_id=shop_id, session=session)
        return {"role": role}