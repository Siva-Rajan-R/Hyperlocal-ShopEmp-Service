from ..repos.shop_repo import ShopRepo
from sqlalchemy import select,update,delete,or_,and_,func,String
from .employee_service import EmployeeService
from schemas.v1.db_schemas.shop_schemas import CreateShopDbSchema,UpdateShopDbSchema,DeleteShopDbSchema
from schemas.v1.request_schemas.shop_schemas import CreateShopSchema,UpdateShopSchema,GetAllShopsSchema,GetShopByIdSchema,DeleteShopSchema,GetShopByUserIdSchema,VerifyShoSchema
from schemas.v1.request_schemas.operating_hours_schemas import CreateOperatingHoursSchema, UpdateOperatingHoursSchema
from schemas.v1.request_schemas.delivery_schemas import CreateDeliverySchema, UpdateDeliverySchema
from schemas.v1.request_schemas.announcement_schemas import CreateAnnouncementSchema, UpdateAnnouncementSchema
from models.service_models.base_service_model import BaseServiceModel
from core.decorators.error_handler_dec import catch_errors
from ..models.employee_model import Employees
from fastapi.exceptions import HTTPException
from hyperlocal_platform.core.enums.timezone_enum import TimeZoneEnum
from sqlalchemy.ext.asyncio import AsyncSession
from hyperlocal_platform.core.utils.uuid_generator import generate_uuid
from typing import Optional,List
from hyperlocal_platform.core.decorators.db_session_handler_dec import start_db_transaction
from icecream import ic

class ShopService(BaseServiceModel):
    def __init__(self, session:AsyncSession):
        super().__init__(session)
        self.shop_repo_obj=ShopRepo(session=session)


    async def create(self, data:CreateShopSchema, user_id:str)-> dict | None:
        has_hours = data.operating_hours is not None and len(data.operating_hours) > 0
        has_delivery = data.delivery_options is not None and len(data.delivery_options) > 0
        if data.visible_online and (not has_hours or not has_delivery):
            raise HTTPException(
                status_code=400,
                detail="Shop operating hours and delivery options are mandatory when shop is visible online."
            )

        shop_id:str=generate_uuid()
        db_payload = data.model_dump(mode="json", exclude={"operating_hours", "delivery_options"})
        data_toadd=CreateShopDbSchema(
            **db_payload,
            id=shop_id,
            user_id=user_id
        )

        res=await self.shop_repo_obj.create(data=data_toadd)
        if res:
            res_dict = dict(res)
            if data.operating_hours:
                for hr in data.operating_hours:
                    await self.shop_repo_obj.add_operating_hours(shop_id=shop_id, data=hr)
            if data.delivery_options:
                for deliv in data.delivery_options:
                    await self.shop_repo_obj.add_delivery_options(shop_id=shop_id, data=deliv)
            return res_dict
        return res
        
    
    async def update(self, data:UpdateShopSchema, user_id:str)-> dict | None:
        ic("Update service started")
        
        # If visible_online is True (or unchanged but is True), validate hours and delivery
        is_online = data.visible_online
        if is_online is None:
            # We can fetch the current online status
            is_online = await self.shop_repo_obj.is_shop_visible_online(data.id)

        if is_online:
            payload_hours_count = len(data.operating_hours) if data.operating_hours is not None else 0
            db_hours_count = await self.shop_repo_obj.count_operating_hours(data.id)
            total_hours = payload_hours_count + db_hours_count

            payload_delivery_count = len(data.delivery_options) if data.delivery_options is not None else 0
            db_delivery_count = await self.shop_repo_obj.count_delivery_options(data.id)
            total_delivery = payload_delivery_count + db_delivery_count

            if total_hours == 0 or total_delivery == 0:
                raise HTTPException(
                    status_code=400,
                    detail="Shop operating hours and delivery are mandatory when shop is visible online. Please add them first."
                )

        db_payload = data.model_dump(mode="json", exclude={"operating_hours", "delivery_options"}, exclude_unset=True, exclude_none=True)
        data_toupdate=UpdateShopDbSchema(**db_payload, user_id=user_id)
        ic(data_toupdate)
        res=await self.shop_repo_obj.update(data=data_toupdate)
        if res:
            res_dict = dict(res)
            if data.operating_hours:
                for hr in data.operating_hours:
                    await self.shop_repo_obj.add_operating_hours(shop_id=data.id, data=hr)
            if data.delivery_options:
                for deliv in data.delivery_options:
                    await self.shop_repo_obj.add_delivery_options(shop_id=data.id, data=deliv)
            return res_dict
        return res

    
    async def delete(self,data:DeleteShopSchema, user_id:str)-> dict | None:
        data_todel=DeleteShopDbSchema(
            **data.model_dump(mode="json"),
            user_id=user_id
        )
        res=await self.shop_repo_obj.delete(data=data_todel)
        return res


    

    async def get(self,data:GetAllShopsSchema)-> List[dict] | list:
        res=await self.shop_repo_obj.get(data=data)
        return res
    

    async def getby_id(self,data:GetShopByIdSchema)-> dict | None:
        res=await self.shop_repo_obj.getby_id(data=data)
        return res
    
    
    async def getby_userid(self,data:GetShopByUserIdSchema)-> List[dict] | list:
        res=await self.shop_repo_obj.getby_userid(data=data)
        return res
    
    async def verify_shop(self,data:VerifyShoSchema)-> bool:
        res=await self.shop_repo_obj.verify_shop(data=data)
        return res
    

    async def search(self, data:GetAllShopsSchema):
        res=await self.shop_repo_obj.search(data=data)
        return res

    # --- Operating Hours Service ---
    async def add_operating_hours(self, shop_id: str, data: CreateOperatingHoursSchema) -> dict | None:
        res = await self.shop_repo_obj.add_operating_hours(shop_id=shop_id, data=data)
        return res

    async def get_operating_hours(self, shop_id: str) -> List[dict]:
        res = await self.shop_repo_obj.get_operating_hours(shop_id=shop_id)
        return res

    async def update_operating_hours(self, hours_id: int, data: UpdateOperatingHoursSchema) -> dict | None:
        res = await self.shop_repo_obj.update_operating_hours(hours_id=hours_id, data=data)
        return res

    async def delete_operating_hours(self, hours_id: int) -> dict | None:
        shop_id = await self.shop_repo_obj.get_shop_id_by_operating_hours_id(hours_id)
        if shop_id:
            is_online = await self.shop_repo_obj.is_shop_visible_online(shop_id)
            if is_online:
                count = await self.shop_repo_obj.count_operating_hours(shop_id)
                if count <= 1:
                    raise HTTPException(
                        status_code=400,
                        detail="Cannot delete the last operating hour. Shop is visible online and operating hours are mandatory."
                    )
        res = await self.shop_repo_obj.delete_operating_hours(hours_id=hours_id)
        return res

    # --- Delivery Options Service ---
    async def add_delivery_options(self, shop_id: str, data: CreateDeliverySchema) -> dict | None:
        res = await self.shop_repo_obj.add_delivery_options(shop_id=shop_id, data=data)
        return res

    async def get_delivery_options(self, shop_id: str) -> List[dict]:
        res = await self.shop_repo_obj.get_delivery_options(shop_id=shop_id)
        return res

    async def update_delivery_options(self, delivery_id: int, data: UpdateDeliverySchema) -> dict | None:
        res = await self.shop_repo_obj.update_delivery_options(delivery_id=delivery_id, data=data)
        return res

    async def delete_delivery_options(self, delivery_id: int) -> dict | None:
        shop_id = await self.shop_repo_obj.get_shop_id_by_delivery_id(delivery_id)
        if shop_id:
            is_online = await self.shop_repo_obj.is_shop_visible_online(shop_id)
            if is_online:
                count = await self.shop_repo_obj.count_delivery_options(shop_id)
                if count <= 1:
                    raise HTTPException(
                        status_code=400,
                        detail="Cannot delete the last delivery option. Shop is visible online and delivery options are mandatory."
                    )
        res = await self.shop_repo_obj.delete_delivery_options(delivery_id=delivery_id)
        return res

    # --- Announcements Service ---
    async def add_announcement(self, shop_id: str, data: CreateAnnouncementSchema) -> dict | None:
        res = await self.shop_repo_obj.add_announcement(shop_id=shop_id, data=data)
        return res

    async def get_announcements(self, shop_id: str) -> List[dict]:
        res = await self.shop_repo_obj.get_announcements(shop_id=shop_id)
        return res

    async def update_announcement(self, announcement_id: int, data: UpdateAnnouncementSchema) -> dict | None:
        res = await self.shop_repo_obj.update_announcement(announcement_id=announcement_id, data=data)
        return res

    async def delete_announcement(self, announcement_id: int) -> dict | None:
        res = await self.shop_repo_obj.delete_announcement(announcement_id=announcement_id)
        return res

