from fastapi import APIRouter,Depends,Query
from infras.primary_db.main import get_pg_async_session,AsyncSession
from typing import Annotated, List, Optional
from ...handlers.employee import HandleEmployeeRequest,CreateEmployeeSchema,UpdateEmployeeSchema,DeleteEmployeeSchema,GetAllEmployeesSchema,GetEmployeeByIdSchema,GetEmployeeByShopIdSchema,SendVerifyEmployeeSchema,VerifyEmployeeTokenSchema
from core.permissions.role_checker import require_permission

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
    import os
    frontend_url = os.getenv("FRONTEND_BASE_URL", "http://localhost:5173")
    try:
        res = await HandleEmployeeRequest(session=session).verify_token(data=VerifyEmployeeTokenSchema(token=token))
        payload = res.get("data", {}) if isinstance(res, dict) else {}
        return RedirectResponse(
            url=f"{frontend_url}/employee/verify?status=success&employee_id={payload.get('employee_id', '')}&shop_id={payload.get('shop_id', '')}",
            status_code=302
        )
    except Exception:
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
@router.get('/by/shop/{shop_id}')
async def get_by_shopid(
    shop_id: str,
    session:PG_ASYNC_SESSION,
    auth_data: Annotated[dict, Depends(require_permission("read_all"))],
    data:GetEmployeeByShopIdSchema=Depends()
):
    data.shop_id = shop_id
    return await HandleEmployeeRequest(session=session).getby_shopid(data=data)


@router.get('/by/{shop_id}/{id}')
async def get_by_empid(
    id: str,
    shop_id: str,
    session:PG_ASYNC_SESSION,
    auth_data: Annotated[dict, Depends(require_permission("read_all"))],
    data:GetEmployeeByIdSchema=Depends()
):
    data.id = id
    data.shop_id = shop_id
    return await HandleEmployeeRequest(session=session).getby_id(data=data)


@router.get('')
async def get_all(
    session:PG_ASYNC_SESSION,
    auth_data: Annotated[dict, Depends(require_permission("read_all"))],
    data:GetAllEmployeesSchema=Depends()
):
    return await HandleEmployeeRequest(session=session).get_all(data=data)