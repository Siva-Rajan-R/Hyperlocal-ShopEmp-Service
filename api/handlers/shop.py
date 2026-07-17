from infras.primary_db.repos.shop_repo import ShopRepo
from sqlalchemy import select,update,delete,or_,and_,func,String
from infras.primary_db.services.shop_service import ShopService
from schemas.v1.db_schemas.shop_schemas import CreateShopDbSchema,UpdateShopDbSchema
from schemas.v1.request_schemas.shop_schemas import CreateShopSchema,UpdateShopSchema,DeleteShopSchema,GetAllShopsSchema,GetShopByUserIdSchema,GetShopByIdSchema,ShopFollowerSchema
from schemas.v1.request_schemas.operating_hours_schemas import CreateOperatingHoursSchema, UpdateOperatingHoursSchema
from schemas.v1.request_schemas.delivery_schemas import CreateDeliverySchema, UpdateDeliverySchema
from schemas.v1.request_schemas.announcement_schemas import CreateAnnouncementSchema, UpdateAnnouncementSchema
from schemas.v1.response_schemas.user_schemas.shop_schemas import (
    ShopCreateResponseSchema, ShopUpdateResponseSchema, ShopDeleteResponseSchema, ShopGetResponseSchema,
    OperatingHoursResponseSchema, DeliveryResponseSchema, AnnouncementResponseSchema
)
from models.service_models.base_service_model import BaseServiceModel
from hyperlocal_platform.core.decorators.db_session_handler_dec import start_db_transaction
from core.decorators.error_handler_dec import catch_errors
from hyperlocal_platform.core.models.req_res_models import SuccessResponseTypDict,ErrorResponseTypDict,BaseResponseTypDict
from infras.primary_db.models.employee_model import Employees
from fastapi.exceptions import HTTPException
from hyperlocal_platform.core.enums.timezone_enum import TimeZoneEnum
from sqlalchemy.ext.asyncio import AsyncSession
from hyperlocal_platform.core.utils.uuid_generator import generate_uuid
from typing import Optional, List
from icecream import ic


class HandleShopRequest:
    def __init__(self, session:AsyncSession):
        self.session=session


    async def create(self, data:CreateShopSchema, user_id:str):
        ic("User_Id => ",user_id)
        res=await ShopService(session=self.session).create(data=data,user_id=user_id)
        if res:
            return SuccessResponseTypDict(
                detail=BaseResponseTypDict(
                    msg="Shop created successfully",
                    status_code=201,
                    success=True
                ),
                data=res
            )
        
    

    async def update(self, data:UpdateShopSchema, user_id:str):
        res=await ShopService(session=self.session).update(data=data,user_id=user_id)
        if res:
            return SuccessResponseTypDict(
                detail=BaseResponseTypDict(
                    msg="Shop updated successfully",
                    success=True,
                    status_code=200
                ),
                data=res
            )
        
        raise HTTPException(
            status_code=404,
            detail=ErrorResponseTypDict(
                msg="Error : Updating Shop",
                description="Invalid Shop Data (id)",
                success=False,
                status_code=404
            )
        )
    

    async def delete(self,data:DeleteShopSchema, user_id:str):
        res=await ShopService(session=self.session).delete(data=data,user_id=user_id)
        if res:
            return SuccessResponseTypDict(
                detail=BaseResponseTypDict(
                    msg="Shop deleted successfully",
                    success=True,
                    status_code=200
                ),
                data=res
            )
        
        raise HTTPException(
            status_code=404,
            detail=ErrorResponseTypDict(
                msg="Error : Deleting shop",
                description="Invalid Shop Data (id,owner)",
                success=False,
                status_code=404
            )
        )
    


    async def get(self,data:GetAllShopsSchema):
        """This repo method for internal use only not to expose it on public !"""
        res=await ShopService(session=self.session).get(data=data)

        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                msg="Shops fetched successfully",
                success=True,
                status_code=200
            ),
            data=res
        )
    


    async def getby_id(self,data:GetShopByIdSchema):
        res=await ShopService(session=self.session).getby_id(data=data)

        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                msg="Shop fetched successfully",
                success=True,
                status_code=200
            ),
            data=res
        )
    


    async def getby_userid(self,data:GetShopByUserIdSchema):
        res=await ShopService(session=self.session).getby_userid(data=data)

        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                msg="Shops fetched successfully",
                success=True,
                status_code=200
            ),
            data=res
        )

    # --- Operating Hours Handlers ---
    async def add_operating_hours(self, shop_id: str, data: CreateOperatingHoursSchema):
        res = await ShopService(session=self.session).add_operating_hours(shop_id=shop_id, data=data)
        if res:
            return SuccessResponseTypDict(
                detail=BaseResponseTypDict(
                    msg="Operating hours added successfully",
                    success=True,
                    status_code=201
                ),
                data=res
            )
        raise HTTPException(status_code=400, detail="Failed to add operating hours")

    async def get_operating_hours(self, shop_id: str):
        res = await ShopService(session=self.session).get_operating_hours(shop_id=shop_id)
        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                msg="Operating hours fetched successfully",
                success=True,
                status_code=200
            ),
            data=res
        )

    async def update_operating_hours(self, hours_id: int, data: UpdateOperatingHoursSchema):
        res = await ShopService(session=self.session).update_operating_hours(hours_id=hours_id, data=data)
        if res:
            return SuccessResponseTypDict(
                detail=BaseResponseTypDict(
                    msg="Operating hours updated successfully",
                    success=True,
                    status_code=200
                ),
                data=res
            )
        raise HTTPException(status_code=404, detail="Operating hours not found or failed to update")

    async def delete_operating_hours(self, hours_id: int):
        res = await ShopService(session=self.session).delete_operating_hours(hours_id=hours_id)
        if res:
            return SuccessResponseTypDict(
                detail=BaseResponseTypDict(
                    msg="Operating hours deleted successfully",
                    success=True,
                    status_code=200
                ),
                data=res
            )
        raise HTTPException(status_code=404, detail="Operating hours not found or failed to delete")

    # --- Delivery Handlers ---
    async def add_delivery_options(self, shop_id: str, data: CreateDeliverySchema):
        res = await ShopService(session=self.session).add_delivery_options(shop_id=shop_id, data=data)
        if res:
            return SuccessResponseTypDict(
                detail=BaseResponseTypDict(
                    msg="Delivery options added successfully",
                    success=True,
                    status_code=201
                ),
                data=res
            )
        raise HTTPException(status_code=400, detail="Failed to add delivery options")

    async def get_delivery_options(self, shop_id: str):
        res = await ShopService(session=self.session).get_delivery_options(shop_id=shop_id)
        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                msg="Delivery options fetched successfully",
                success=True,
                status_code=200
            ),
            data=res
        )

    async def update_delivery_options(self, delivery_id: int, data: UpdateDeliverySchema):
        res = await ShopService(session=self.session).update_delivery_options(delivery_id=delivery_id, data=data)
        if res:
            return SuccessResponseTypDict(
                detail=BaseResponseTypDict(
                    msg="Delivery options updated successfully",
                    success=True,
                    status_code=200
                ),
                data=res
            )
        raise HTTPException(status_code=404, detail="Delivery options not found or failed to update")

    async def delete_delivery_options(self, delivery_id: int):
        res = await ShopService(session=self.session).delete_delivery_options(delivery_id=delivery_id)
        if res:
            return SuccessResponseTypDict(
                detail=BaseResponseTypDict(
                    msg="Delivery options deleted successfully",
                    success=True,
                    status_code=200
                ),
                data=res
            )
        raise HTTPException(status_code=404, detail="Delivery options not found or failed to delete")

    # --- Announcement Handlers ---
    async def add_announcement(self, shop_id: str, data: CreateAnnouncementSchema):
        res = await ShopService(session=self.session).add_announcement(shop_id=shop_id, data=data)
        if res:
            return SuccessResponseTypDict(
                detail=BaseResponseTypDict(
                    msg="Announcement added successfully",
                    success=True,
                    status_code=201
                ),
                data=res
            )
        raise HTTPException(status_code=400, detail="Failed to add announcement")

    async def get_announcements(self, shop_id: str):
        res = await ShopService(session=self.session).get_announcements(shop_id=shop_id)
        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                msg="Announcements fetched successfully",
                success=True,
                status_code=200
            ),
            data=res
        )

    async def update_announcement(self, data: UpdateAnnouncementSchema,shop_id:str):
        res = await ShopService(session=self.session).update_announcement(data=data,shop_id=shop_id)
        if res:
            return SuccessResponseTypDict(
                detail=BaseResponseTypDict(
                    msg="Announcement updated successfully",
                    success=True,
                    status_code=200
                ),
                data=res
            )
        raise HTTPException(status_code=404, detail="Announcement not found or failed to update")

    async def delete_announcement(self, announcement_id: int,shop_id:str):
        res = await ShopService(session=self.session).delete_announcement(announcement_id=announcement_id,shop_id=shop_id)
        if res:
            return SuccessResponseTypDict(
                detail=BaseResponseTypDict(
                    msg="Announcement deleted successfully",
                    success=True,
                    status_code=200
                ),
                data=res
            )
        raise HTTPException(status_code=404, detail="Announcement not found or failed to delete")

    async def follow_shop(self, data: ShopFollowerSchema):
        res = await ShopService(session=self.session).follow_shop(data=data)
        if res:
            return SuccessResponseTypDict(
                detail=BaseResponseTypDict(
                    msg="Shop followed successfully",
                    success=True,
                    status_code=200
                ),
                data=res
            )
        raise HTTPException(status_code=400, detail="Failed to follow shop")

    async def unfollow_shop(self, shop_id: str, user_id: str):
        res = await ShopService(session=self.session).unfollow_shop(shop_id=shop_id, user_id=user_id)
        if res:
            return SuccessResponseTypDict(
                detail=BaseResponseTypDict(
                    msg="Shop unfollowed successfully",
                    success=True,
                    status_code=200
                ),
                data={"shop_id": shop_id, "user_id": user_id}
            )
        raise HTTPException(status_code=404, detail="Follow connection not found or failed to delete")

    async def get_shop_followers(self, shop_id: str):
        res = await ShopService(session=self.session).get_shop_followers(shop_id=shop_id)
        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                msg="Shop followers fetched successfully",
                success=True,
                status_code=200
            ),
            data=res
        )

    async def get_user_followed_shops(self, user_id: str):
        res = await ShopService(session=self.session).get_user_followed_shops(user_id=user_id)
        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                msg="User followed shops fetched successfully",
                success=True,
                status_code=200
            ),
            data=res
        )


