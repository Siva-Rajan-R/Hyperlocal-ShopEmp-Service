from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from infras.primary_db.services.user_service import UserService
from infras.primary_db.services.shop_service import ShopService
from infras.primary_db.services.employee_service import EmployeeService
from schemas.v1.request_schemas.shop_schemas import GetShopByUserIdSchema
from schemas.v1.response_schemas.user_schemas.shop_schemas import ShopGetResponseSchema
from hyperlocal_platform.core.models.req_res_models import SuccessResponseTypDict, BaseResponseTypDict, ErrorResponseTypDict
from icecream import ic


class HandleAuthRequest:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_service_obj = UserService(session=self.session)
        self.shop_service_obj = ShopService(session=self.session)
        self.employee_service_obj = EmployeeService(session=self.session)

    async def check_user(self, email: str, name: str = "Anonymous", mobile_number: str = ""):
        user = await self.user_service_obj.get_or_create_user(name=name, email=email, mobile_number=mobile_number)
        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                msg="User checked/created successfully",
                success=True,
                status_code=200
            ),
            data={
                "id": user["id"],
                "name": user["name"],
                "email": user["email"],
                "mobile_number": user["mobile_number"]
            }
        )

    async def check_shop(self, user_id: str):
        # Checks if shop exists for user_id
        shops = await self.shop_service_obj.getby_userid(GetShopByUserIdSchema(user_id=user_id))
        if shops:
            return SuccessResponseTypDict(
                detail=BaseResponseTypDict(
                    msg="Shop exists for this user",
                    success=True,
                    status_code=200
                ),
                data={
                    "exists": True,
                    "shops": shops
                }
            )
        
        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                msg="No shop exists for this user",
                success=True,
                status_code=200
            ),
            data={
                "exists": False,
                "shops": []
            }
        )

    async def verify_employee(self, token: str):
        res = await self.employee_service_obj.accept_employee(token=token)
        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                msg="Employee invitation accepted and verified successfully",
                success=True,
                status_code=200
            ),
            data=res
        )
