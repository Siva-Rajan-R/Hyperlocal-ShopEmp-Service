from fastapi import Header, HTTPException, Depends, Request
from infras.primary_db.main import get_pg_async_session, AsyncSession
from infras.primary_db.repos.shop_repo import ShopRepo
from infras.primary_db.repos.employee_repo import EmployeeRepo
from schemas.v1.request_schemas.shop_schemas import GetShopByIdSchema
from core.data_formats.enums.employee_enums import EmployeeRoleEnums
from typing import Optional, Set
from icecream import ic

ROLE_PERMISSIONS = {
    "OWNER": {
        "create_shop", "delete_shop", "create_employee", "delete_employee", 
        "update_shop", "update_employee", "read_all", "create_billing"
    },
    "SUPER_ADMIN": {
        "create_employee", "delete_employee", "update_shop", "update_employee", 
        "read_all", "create_billing"
    },
    "ADMIN": {
        "update_shop", "update_employee", "read_all", "create_billing"
    },
    "BILLER": {
        "read_all", "create_billing"
    },
}

async def get_user_role(user_id: str, shop_id: str, session: AsyncSession) -> Optional[str]:
    # 1. Check if user is the shop OWNER
    shop_repo = ShopRepo(session=session)
    shop = await shop_repo.getby_id(GetShopByIdSchema(shop_id=shop_id))
    if shop and shop.get("user_id") == user_id:
        return "OWNER"
    
    # 2. Check if user is an accepted employee of the shop
    employee_repo = EmployeeRepo(session=session)
    employee = await employee_repo.is_employee_exists(employee_account_id=user_id, shop_id=shop_id)
    # Check if employee exists and is accepted
    if employee and employee.get("accepted") is True:
        return employee.get("role")
    
    return None

def require_permission(action: str):
    async def dependency(
        request: Request,
        x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
        x_shop_id: Optional[str] = Header(None, alias="X-Shop-Id"),
        session: AsyncSession = Depends(get_pg_async_session)
    ):
        # Resolve user_id and shop_id
        user_id = x_user_id
        shop_id = x_shop_id

        # Fallback to path params if headers are missing
        path_params = request.path_params
        if not shop_id and "shop_id" in path_params:
            shop_id = path_params["shop_id"]
        
        # Fallback to query params
        query_params = request.query_params
        if not user_id and "user_id" in query_params:
            user_id = query_params["user_id"]
        if not shop_id and "shop_id" in query_params:
            shop_id = query_params["shop_id"]

        # If it's a create shop request, we only need user_id (everyone can create a shop)
        if action == "create_shop":
            if not user_id:
                raise HTTPException(status_code=401, detail="X-User-Id header or user_id query parameter is required")
            return user_id

        if not user_id or not shop_id:
            raise HTTPException(status_code=401, detail="X-User-Id and X-Shop-Id headers (or equivalent params) are required")
        role="owner"
        if action=="create_shop":
            role = await get_user_role(user_id=user_id, shop_id=shop_id, session=session)
            ic(role)
            if not role:
                raise HTTPException(status_code=403, detail="Access denied: Not an authorized employee/owner of this shop")

            allowed_actions = ROLE_PERMISSIONS.get(role, set())
            if action not in allowed_actions:
                raise HTTPException(status_code=403, detail=f"Access denied: Role '{role}' does not have '{action}' permission")

        ic({"user_id": user_id, "shop_id": shop_id, "role": role})
        return {"user_id": user_id, "shop_id": shop_id, "role": role}

    return dependency
