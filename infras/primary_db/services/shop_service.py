from ..repos.shop_repo import ShopRepo
from sqlalchemy import select,update,delete,or_,and_,func,String
from .employee_service import EmployeeService
from schemas.v1.db_schemas.shop_schemas import CreateShopDbSchema,UpdateShopDbSchema,DeleteShopDbSchema
from schemas.v1.request_schemas.shop_schemas import CreateShopSchema,UpdateShopSchema,GetAllShopsSchema,GetShopByIdSchema,DeleteShopSchema,GetShopByUserIdSchema,VerifyShoSchema,ShopFollowerSchema
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
            # Map categories and datas
            cats = res_dict.get('categories', [])
            res_dict['category'] = cats[0] if cats else ''
            res_dict['image_urls'] = []

            hours_list = []
            if data.operating_hours:
                for hr in data.operating_hours:
                    h_res = await self.shop_repo_obj.add_operating_hours(shop_id=shop_id, data=hr)
                    if h_res:
                        hours_list.append(dict(h_res))
            delivery_list = []
            if data.delivery_options:
                for deliv in data.delivery_options:
                    d_res = await self.shop_repo_obj.add_delivery_options(shop_id=shop_id, data=deliv)
                    if d_res:
                        delivery_list.append(dict(d_res))
            
            # Sync to MongoDB
            try:
                from ...read_db.services.shop_service import ReadDbShopService
                from ...read_db.models.shop_model import ReadDbShopCreateModel
                
                def make_serializable(item):
                    if not item:
                        return item
                    new_item = dict(item)
                    for k, v in new_item.items():
                        if hasattr(v, 'isoformat'):
                            new_item[k] = v.isoformat()
                        elif hasattr(v, 'strftime'):
                            new_item[k] = str(v)
                    return new_item
                
                mongo_payload = ReadDbShopCreateModel(
                    id=res_dict["id"],
                    ui_id=res_dict.get("ui_id"),
                    sequence_id=res_dict.get("sequence_id"),
                    user_id=res_dict["user_id"],
                    name=res_dict["name"],
                    description=res_dict.get("description"),
                    tagline=res_dict.get("tagline"),
                    categories=res_dict.get("categories") or [],
                    business_infos=res_dict.get("business_infos") or {},
                    address=res_dict.get("address") or {},
                    banner_url=res_dict.get("banner_url"),
                    logo_url=res_dict.get("logo_url"),
                    additional_infos=res_dict.get("additional_infos") or {},
                    visible_online=res_dict.get("visible_online", False),
                    operating_hours=[make_serializable(h) for h in hours_list],
                    delivery_options=[make_serializable(d) for d in delivery_list],
                    announcements=[]
                )
                await ReadDbShopService(payload=mongo_payload).create()
            except Exception as e:
                ic(f"Failed to sync shop to MongoDB: {e}")

            # Emit "Shop Created" event to RabbitMQ
            try:
                from messaging.main import RabbitMQMessagingConfig
                from aio_pika import ExchangeType
                rabbitmq_msg_obj = RabbitMQMessagingConfig()
                await rabbitmq_msg_obj.create_exchange(name="activity_logs.exchange", exchange_type=ExchangeType.TOPIC)
                
                payload = {
                    "shop_id": shop_id,
                    "user_name": "system",
                    "service": "Shop",
                    "action": "CREATE",
                    "entity_type": "Shop",
                    "entity_id": shop_id,
                    "description": f"Created new shop: {data.name}",
                    "changes": []
                }
                
                headers = {
                    "routing_key": "utility.service.routing.key",
                    "exchange_name": "utility.service.exchange",
                    "entity_name": "init_defaults",
                    "service_name": "UTILITY",
                    "saga_id": "None",
                    "reply_key": "None",
                    "reply_exchange": "None",
                    "reply_entity_name": "None",
                    "body": payload
                }
                
                await rabbitmq_msg_obj.publish_event(
                    routing_key="utility.service.routing.key",
                    exchange_name="utility.service.exchange",
                    payload=payload,
                    headers=headers
                )
            except Exception as msg_err:
                ic(f"Failed to publish shop created event: {msg_err}")

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
            cats = res_dict.get('categories', [])
            res_dict['category'] = cats[0] if cats else ''
            res_dict['image_urls'] = []

            hours_list = []
            if data.operating_hours:
                for hr in data.operating_hours:
                    h_res = await self.shop_repo_obj.add_operating_hours(shop_id=data.id, data=hr)
                    if h_res:
                        hours_list.append(dict(h_res))
            delivery_list = []
            if data.delivery_options:
                for deliv in data.delivery_options:
                    d_res = await self.shop_repo_obj.add_delivery_options(shop_id=data.id, data=deliv)
                    if d_res:
                        delivery_list.append(dict(d_res))

            # Sync to MongoDB
            try:
                from ...read_db.services.shop_service import ReadDbShopService
                from ...read_db.models.shop_model import ReadDbShopUpdateModel

                def make_serializable(item):
                    if not item:
                        return item
                    new_item = dict(item)
                    for k, v in new_item.items():
                        if hasattr(v, 'isoformat'):
                            new_item[k] = v.isoformat()
                        elif hasattr(v, 'strftime'):
                            new_item[k] = str(v)
                    return new_item

                mongo_update = ReadDbShopUpdateModel(
                    name=res_dict.get("name"),
                    description=res_dict.get("description"),
                    tagline=res_dict.get("tagline"),
                    categories=res_dict.get("categories"),
                    business_infos=res_dict.get("business_infos"),
                    address=res_dict.get("address"),
                    banner_url=res_dict.get("banner_url"),
                    logo_url=res_dict.get("logo_url"),
                    additional_infos=res_dict.get("additional_infos"),
                    visible_online=res_dict.get("visible_online")
                )
                await ReadDbShopService(
                    payload=mongo_update,
                    conditions={"id": data.id}
                ).update()

                if hours_list:
                    for hr in hours_list:
                        await ReadDbShopService().add_operating_hours(shop_id=data.id, hours=make_serializable(hr))
                if delivery_list:
                    for dl in delivery_list:
                        await ReadDbShopService().add_delivery_options(shop_id=data.id, delivery=make_serializable(dl))
            except Exception as e:
                ic(f"Failed to sync shop update to MongoDB: {e}")

            return res_dict
        return res

    
    async def delete(self,data:DeleteShopSchema, user_id:str)-> dict | None:
        data_todel=DeleteShopDbSchema(
            **data.model_dump(mode="json"),
            user_id=user_id
        )
        res=await self.shop_repo_obj.delete(data=data_todel)
        if res:
            try:
                from ...read_db.services.shop_service import ReadDbShopService
                await ReadDbShopService(conditions={"id": data.shop_id}).delete()
            except Exception as e:
                ic(f"Failed to sync shop deletion to MongoDB: {e}")
        return res


    

    async def get(self,data:GetAllShopsSchema)-> List[dict] | list:
        try:
            from ...read_db.services.shop_service import ReadDbShopService
            read_service = ReadDbShopService(payload=None, conditions={})
            res = await read_service.get(query=data.query, limit=data.limit, offset=data.offset)
        except Exception as e:
            ic(f"Failed to fetch shops from MongoDB: {e}")
            res = None

        if not res:
            res=await self.shop_repo_obj.get(data=data)
            res = [dict(r) for r in res]
            for r in res:
                cats = r.get('categories', [])
                r['category'] = cats[0] if cats else ''
                r['datas'] = r.pop('additional_infos', {}) or {}
                r['image_urls'] = []
        return res
    

    async def getby_id(self,data:GetShopByIdSchema)-> dict | None:
        try:
            from ...read_db.services.shop_service import ReadDbShopService
            read_service = ReadDbShopService(payload=None, conditions={"id": data.shop_id})
            res = await read_service.get_one(queries={"id": data.shop_id})
        except Exception as e:
            ic(f"Failed to fetch shop from MongoDB: {e}")
            res = None

        if not res:
            res=await self.shop_repo_obj.getby_id(data=data)
            if res:
                res = dict(res)
                cats = res.get('categories', [])
                res['category'] = cats[0] if cats else ''
                res['datas'] = res.pop('additional_infos', {}) or {}
                res['image_urls'] = []
        return res
    
    
    async def getby_userid(self,data:GetShopByUserIdSchema)-> List[dict] | list:
        try:
            from ...read_db.services.shop_service import ReadDbShopService
            read_service = ReadDbShopService(payload=None, conditions={})
            res = await read_service.getby_queries(queries={"user_id": data.user_id})
        except Exception as e:
            ic(f"Failed to fetch shops from MongoDB: {e}")
            res = None

        if not res:
            res=await self.shop_repo_obj.getby_userid(data=data)
            if res:
                res = [dict(r) for r in res]
                for r in res:
                    cats = r.get('categories', [])
                    r['category'] = cats[0] if cats else ''
                    r['datas'] = r.pop('additional_infos', {}) or {}
                    r['image_urls'] = []
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
        if res:
            try:
                from ...read_db.services.shop_service import ReadDbShopService
                def make_serializable(item):
                    if not item:
                        return item
                    new_item = dict(item)
                    for k, v in new_item.items():
                        if hasattr(v, 'isoformat'):
                            new_item[k] = v.isoformat()
                        elif hasattr(v, 'strftime'):
                            new_item[k] = str(v)
                    return new_item
                await ReadDbShopService().add_operating_hours(shop_id=shop_id, hours=make_serializable(res))
            except Exception as e:
                ic(f"Failed to sync operating hours to MongoDB: {e}")
        return res

    async def get_operating_hours(self, shop_id: str) -> List[dict]:
        res = await self.shop_repo_obj.get_operating_hours(shop_id=shop_id)
        return res

    async def update_operating_hours(self, hours_id: int, data: UpdateOperatingHoursSchema) -> dict | None:
        res = await self.shop_repo_obj.update_operating_hours(hours_id=hours_id, data=data)
        if res:
            try:
                from ...read_db.services.shop_service import ReadDbShopService
                def make_serializable(item):
                    if not item:
                        return item
                    new_item = dict(item)
                    for k, v in new_item.items():
                        if hasattr(v, 'isoformat'):
                            new_item[k] = v.isoformat()
                        elif hasattr(v, 'strftime'):
                            new_item[k] = str(v)
                    return new_item
                await ReadDbShopService().update_operating_hours(hours_id=hours_id, hours=make_serializable(res))
            except Exception as e:
                ic(f"Failed to sync operating hours update to MongoDB: {e}")
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
        if res:
            try:
                from ...read_db.services.shop_service import ReadDbShopService
                await ReadDbShopService().delete_operating_hours(hours_id=hours_id)
            except Exception as e:
                ic(f"Failed to sync operating hours deletion to MongoDB: {e}")
        return res

    # --- Delivery Options Service ---
    async def add_delivery_options(self, shop_id: str, data: CreateDeliverySchema) -> dict | None:
        res = await self.shop_repo_obj.add_delivery_options(shop_id=shop_id, data=data)
        if res:
            try:
                from ...read_db.services.shop_service import ReadDbShopService
                def make_serializable(item):
                    if not item:
                        return item
                    new_item = dict(item)
                    for k, v in new_item.items():
                        if hasattr(v, 'isoformat'):
                            new_item[k] = v.isoformat()
                        elif hasattr(v, 'strftime'):
                            new_item[k] = str(v)
                    return new_item
                await ReadDbShopService().add_delivery_options(shop_id=shop_id, delivery=make_serializable(res))
            except Exception as e:
                ic(f"Failed to sync delivery options to MongoDB: {e}")
        return res

    async def get_delivery_options(self, shop_id: str) -> List[dict]:
        res = await self.shop_repo_obj.get_delivery_options(shop_id=shop_id)
        return res

    async def update_delivery_options(self, delivery_id: int, data: UpdateDeliverySchema) -> dict | None:
        res = await self.shop_repo_obj.update_delivery_options(delivery_id=delivery_id, data=data)
        if res:
            try:
                from ...read_db.services.shop_service import ReadDbShopService
                def make_serializable(item):
                    if not item:
                        return item
                    new_item = dict(item)
                    for k, v in new_item.items():
                        if hasattr(v, 'isoformat'):
                            new_item[k] = v.isoformat()
                        elif hasattr(v, 'strftime'):
                            new_item[k] = str(v)
                    return new_item
                await ReadDbShopService().update_delivery_options(delivery_id=delivery_id, delivery=make_serializable(res))
            except Exception as e:
                ic(f"Failed to sync delivery options update to MongoDB: {e}")
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
        if res:
            try:
                from ...read_db.services.shop_service import ReadDbShopService
                await ReadDbShopService().delete_delivery_options(delivery_id=delivery_id)
            except Exception as e:
                ic(f"Failed to sync delivery options deletion to MongoDB: {e}")
        return res

    # --- Announcements Service ---
    async def add_announcement(self, shop_id: str, data: CreateAnnouncementSchema) -> dict | None:
        res = await self.shop_repo_obj.add_announcement(shop_id=shop_id, data=data)
        if res:
            try:
                from ...read_db.services.shop_service import ReadDbShopService
                def make_serializable(item):
                    if not item:
                        return item
                    new_item = dict(item)
                    for k, v in new_item.items():
                        if hasattr(v, 'isoformat'):
                            new_item[k] = v.isoformat()
                        elif hasattr(v, 'strftime'):
                            new_item[k] = str(v)
                    return new_item
                await ReadDbShopService().add_announcement(shop_id=shop_id, announcement=make_serializable(res))
            except Exception as e:
                ic(f"Failed to sync announcement to MongoDB: {e}")
        return res

    async def get_announcements(self, shop_id: str) -> List[dict]:
        res = await self.shop_repo_obj.get_announcements(shop_id=shop_id)
        return res

    async def update_announcement(self,data: UpdateAnnouncementSchema,shop_id:str) -> dict | None:
        res = await self.shop_repo_obj.update_announcement(data=data,shop_id=shop_id)
        if res:
            try:
                from ...read_db.services.shop_service import ReadDbShopService
                def make_serializable(item):
                    if not item:
                        return item
                    new_item = dict(item)
                    for k, v in new_item.items():
                        if hasattr(v, 'isoformat'):
                            new_item[k] = v.isoformat()
                        elif hasattr(v, 'strftime'):
                            new_item[k] = str(v)
                    return new_item
                await ReadDbShopService().update_announcement(announcement_id=data.id, announcement=make_serializable(res))
            except Exception as e:
                ic(f"Failed to sync announcement update to MongoDB: {e}")
        return res

    async def delete_announcement(self, announcement_id: int,shop_id:str) -> dict | None:
        res = await self.shop_repo_obj.delete_announcement(announcement_id=announcement_id,shop_id=shop_id)
        if res:
            try:
                from ...read_db.services.shop_service import ReadDbShopService
                await ReadDbShopService().delete_announcement(announcement_id=announcement_id)
            except Exception as e:
                ic(f"Failed to sync announcement deletion to MongoDB: {e}")
        return res

    # --- Shop Followers Service ---
    async def follow_shop(self, data: ShopFollowerSchema) -> dict | None:
        res = await self.shop_repo_obj.follow_shop(shop_id=data.shop_id, user_id=data.user_id)
        return res

    async def unfollow_shop(self, shop_id: str, user_id: str) -> bool:
        res = await self.shop_repo_obj.unfollow_shop(shop_id=shop_id, user_id=user_id)
        return res

    async def get_shop_followers(self, shop_id: str) -> List[str]:
        res = await self.shop_repo_obj.get_shop_followers(shop_id=shop_id)
        return res

    async def get_user_followed_shops(self, user_id: str) -> List[dict]:
        res = await self.shop_repo_obj.get_user_followed_shops(user_id=user_id)
        return res


