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
        "create_shop", "delete_shop", "create_employee", "delete_employee", "update_employee", "read_employee",
        "update_shop", "read_all", "create_billing",
        "create_supplier", "update_supplier", "delete_supplier",
        "create_product", "update_product", "delete_product",
        "create_purchase", "update_purchase", "delete_purchase",
        "create_customer", "update_customer", "delete_customer",
        "create_stock_adj", "update_stock_adj",
        "create_order", "update_order", "delete_order"
    },
    "SUPER_ADMIN": {
        "update_shop", "read_employee",
        "read_all", "create_billing",
        "create_supplier", "update_supplier", "delete_supplier",
        "create_product", "update_product", "delete_product",
        "create_purchase", "update_purchase", "delete_purchase",
        "create_customer", "update_customer", "delete_customer",
        "create_stock_adj", "update_stock_adj",
        "create_order", "update_order", "delete_order"
    },
    "ADMIN": {
        "update_shop",
        "read_all", "create_billing",
        "create_supplier", "update_supplier",
        "create_product", "update_product",
        "create_purchase", "update_purchase",
        "create_customer", "update_customer",
        "create_stock_adj", "update_stock_adj",
        "create_order", "update_order"
    },
    "BILLER": {
        "read_all", "create_billing", "create_order", "update_order",
        "create_customer", "update_customer"
    },
}

ROLE_MODULES = {
    "OWNER": ["DASHBOARD", "PRODUCTS", "SUPPLIERS", "PURCHASES", "INVENTORY", "BILLING", "SALES", "CUSTOMERS", "EMPLOYEES", "ONLINE_ORDERS", "DIGITAL_STORE"],
    "SUPER_ADMIN": ["DASHBOARD", "PRODUCTS", "SUPPLIERS", "PURCHASES", "INVENTORY", "BILLING", "SALES", "CUSTOMERS", "ONLINE_ORDERS", "DIGITAL_STORE"],
    "ADMIN": ["DASHBOARD", "PRODUCTS", "SUPPLIERS", "PURCHASES", "INVENTORY", "BILLING", "SALES", "CUSTOMERS", "ONLINE_ORDERS", "DIGITAL_STORE"],
    "BILLER": ["DASHBOARD", "BILLING", "SALES", "CUSTOMERS", "PRODUCTS", "ONLINE_ORDERS"],
    "USER": ["DASHBOARD", "PRODUCTS", "INVENTORY"],
    "MANAGER": ["DASHBOARD", "PRODUCTS", "INVENTORY", "SALES", "CUSTOMERS", "ONLINE_ORDERS", "DIGITAL_STORE"],
}

import time

# In-memory TTL cache: (user_id, shop_id) -> (role, expire_timestamp)
_USER_ROLE_CACHE: dict = {}
_ROLE_CACHE_TTL = 60.0  # Cache roles for 60 seconds

def invalidate_user_role_cache(user_id: Optional[str] = None, shop_id: Optional[str] = None):
    global _USER_ROLE_CACHE
    if not user_id and not shop_id:
        _USER_ROLE_CACHE.clear()
        return
    keys_to_remove = [
        k for k in _USER_ROLE_CACHE.keys()
        if (not user_id or k[0] == user_id) and (not shop_id or k[1] == shop_id)
    ]
    for k in keys_to_remove:
        _USER_ROLE_CACHE.pop(k, None)

async def get_user_role(user_id: str, shop_id: str, session: AsyncSession) -> Optional[str]:
    now = time.time()
    cache_key = (user_id, shop_id)
    cached = _USER_ROLE_CACHE.get(cache_key)
    if cached and (now < cached[1]):
        return cached[0]

    role = None
    # 1. Check if user is the shop OWNER
    shop_repo = ShopRepo(session=session)
    shop = await shop_repo.getby_id(GetShopByIdSchema(shop_id=shop_id))
    if shop and shop.get("user_id") == user_id:
        role = "OWNER"
    else:
        # 2. Check if user is an accepted employee of the shop
        employee_repo = EmployeeRepo(session=session)
        employee = await employee_repo.is_employee_exists(employee_account_id=user_id, shop_id=shop_id)
        # Check if employee exists and is accepted
        if employee and employee.get("accepted") is True:
            role = employee.get("role")
    
    _USER_ROLE_CACHE[cache_key] = (role, now + _ROLE_CACHE_TTL)
    return role

def require_permission(action: str):
    async def dependency(
        request: Request,
        session: AsyncSession = Depends(get_pg_async_session)
    ):
        import json
        x_user_infos = request.headers.get("X-User-Infos")
        user_id = None
        token_role = None

        if x_user_infos:
            try:
                user_data = json.loads(x_user_infos)
                user_id = user_data.get("user_id")
                token_role = user_data.get("role")
            except Exception as e:
                pass

        # Resolve shop_id
        shop_id = request.headers.get("X-Shop-Id")
        path_params = request.path_params
        if not shop_id and "shop_id" in path_params:
            shop_id = path_params["shop_id"]
        
        query_params = request.query_params
        if not shop_id and "shop_id" in query_params:
            shop_id = query_params["shop_id"]

        if not user_id:
            raise HTTPException(status_code=401, detail="User identification is required (missing X-User-Infos)")

        if action == "create_shop":
            return user_id

        if not shop_id:
            raise HTTPException(status_code=400, detail="Shop identification (X-Shop-Id or query/path param) is required")

        role = token_role
        if not role:
            role = await get_user_role(user_id=user_id, shop_id=shop_id, session=session)
        
        if not role:
            raise HTTPException(status_code=403, detail="Access denied: Not an authorized employee/owner of this shop")

        allowed_actions = ROLE_PERMISSIONS.get(role, set())
        if action not in allowed_actions:
            raise HTTPException(status_code=403, detail=f"Access denied: Role '{role}' does not have '{action}' permission")

        return {"user_id": user_id, "shop_id": shop_id, "role": role}

    return dependency
