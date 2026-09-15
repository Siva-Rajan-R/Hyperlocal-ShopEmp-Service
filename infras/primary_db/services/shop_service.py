from core.utils.user_context import get_activity_log_user_info
from infras.primary_db.repos.shop_repo import ShopRepo
from sqlalchemy import select,update,delete,or_,and_,func,String
import math
from infras.primary_db.services.employee_service import EmployeeService
from schemas.v1.db_schemas.shop_schemas import CreateShopDbSchema,UpdateShopDbSchema,DeleteShopDbSchema
from schemas.v1.request_schemas.shop_schemas import CreateShopSchema,UpdateShopSchema,GetAllShopsSchema,GetShopByIdSchema,DeleteShopSchema,GetShopByUserIdSchema,VerifyShoSchema,ShopFollowerSchema,GetBulkShopsByIdSchema,GetGeofencedShopsSchema
from schemas.v1.request_schemas.operating_hours_schemas import CreateOperatingHoursSchema, UpdateOperatingHoursSchema
from schemas.v1.request_schemas.delivery_schemas import CreateDeliverySchema, UpdateDeliverySchema
from schemas.v1.request_schemas.announcement_schemas import CreateAnnouncementSchema, UpdateAnnouncementSchema
from models.service_models.base_service_model import BaseServiceModel
from core.decorators.error_handler_dec import catch_errors
from infras.primary_db.models.employee_model import Employees
from infras.primary_db.models.shop_model import ShopOperatingHours, ShopDelivery
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
        db_payload = data.model_dump(mode="json", exclude={"operating_hours", "delivery_options", "visibility_only", "is_ordering_enabled"})
        
        # Resolve visibility_only and is_ordering_enabled into additional_infos
        add_infos = db_payload.get("additional_infos") or {}
        vis_only = data.visibility_only if data.visibility_only is not None else add_infos.get("visibility_only", False)
        ord_enabled = data.is_ordering_enabled if data.is_ordering_enabled is not None else add_infos.get("is_ordering_enabled", not vis_only)
        if vis_only:
            ord_enabled = False
        add_infos["visibility_only"] = vis_only
        add_infos["is_ordering_enabled"] = ord_enabled
        db_payload["additional_infos"] = add_infos

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
            res_dict['visibility_only'] = vis_only
            res_dict['is_ordering_enabled'] = ord_enabled
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
                from infras.read_db.services.shop_service import ReadDbShopService
                from infras.read_db.models.shop_model import ReadDbShopCreateModel
                
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
                    additional_infos=add_infos,
                    visible_online=res_dict.get("visible_online", False),
                    visibility_only=vis_only,
                    is_ordering_enabled=ord_enabled,
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
                    "categories": res_dict.get("categories") or [],
                    **get_activity_log_user_info(),
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
        
        # Only validate hours and delivery when explicitly setting visible_online=True
        is_turning_online = data.visible_online is True
        if is_turning_online:
            payload_hours_count = len(data.operating_hours) if data.operating_hours is not None else 0
            db_hours_count = await self.shop_repo_obj.count_operating_hours(data.id) if data.operating_hours is None else 0
            total_hours = payload_hours_count + db_hours_count

            payload_delivery_count = len(data.delivery_options) if data.delivery_options is not None else 0
            db_delivery_count = await self.shop_repo_obj.count_delivery_options(data.id) if data.delivery_options is None else 0
            total_delivery = payload_delivery_count + db_delivery_count

            if total_hours == 0 or total_delivery == 0:
                raise HTTPException(
                    status_code=400,
                    detail="Shop operating hours and delivery are mandatory when shop is visible online. Please add them first."
                )

        db_payload = data.model_dump(mode="json", exclude={"operating_hours", "delivery_options", "visibility_only", "is_ordering_enabled"}, exclude_unset=True, exclude_none=True)
        
        # Handle visibility_only and is_ordering_enabled in additional_infos
        if data.visibility_only is not None or data.is_ordering_enabled is not None:
            existing_shop = await self.shop_repo_obj.get_shop_with_relations(data.id)
            existing_add = (existing_shop.get("additional_infos") if existing_shop else {}) or {}
            if "additional_infos" in db_payload:
                existing_add.update(db_payload["additional_infos"])
            if data.visibility_only is not None:
                existing_add["visibility_only"] = data.visibility_only
                if data.visibility_only:
                    existing_add["is_ordering_enabled"] = False
            if data.is_ordering_enabled is not None and not existing_add.get("visibility_only"):
                existing_add["is_ordering_enabled"] = data.is_ordering_enabled
            db_payload["additional_infos"] = existing_add

        data_toupdate=UpdateShopDbSchema(**db_payload, user_id=user_id)
        ic(data_toupdate)
        res=await self.shop_repo_obj.update(data=data_toupdate)
        if res:
            res_dict = dict(res)
            cats = res_dict.get('categories', [])
            res_dict['category'] = cats[0] if cats else ''
            add_infos = res_dict.get('additional_infos') or {}
            res_dict['visibility_only'] = add_infos.get('visibility_only', False)
            res_dict['is_ordering_enabled'] = add_infos.get('is_ordering_enabled', not res_dict['visibility_only'])
            res_dict['image_urls'] = []

            hours_list = []
            if data.operating_hours is not None:
                await self.session.execute(delete(ShopOperatingHours).where(ShopOperatingHours.shop_id == data.id))
                for hr in data.operating_hours:
                    h_res = await self.shop_repo_obj.add_operating_hours(shop_id=data.id, data=hr)
                    if h_res:
                        hours_list.append(dict(h_res))
            delivery_list = []
            if data.delivery_options is not None:
                await self.session.execute(delete(ShopDelivery).where(ShopDelivery.shop_id == data.id))
                for deliv in data.delivery_options:
                    d_res = await self.shop_repo_obj.add_delivery_options(shop_id=data.id, data=deliv)
                    if d_res:
                        delivery_list.append(dict(d_res))

            # Sync to MongoDB
            try:
                from infras.read_db.services.shop_service import ReadDbShopService
                from infras.read_db.models.shop_model import ReadDbShopUpdateModel

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
                    visible_online=res_dict.get("visible_online"),
                    visibility_only=res_dict.get("visibility_only"),
                    is_ordering_enabled=res_dict.get("is_ordering_enabled")
                )
                await ReadDbShopService(
                    payload=mongo_update,
                    conditions={"id": data.id}
                ).update()

                if data.operating_hours is not None:
                    await ReadDbShopService().set_operating_hours(
                        shop_id=data.id,
                        hours_list=[make_serializable(hr) for hr in hours_list]
                    )
                if data.delivery_options is not None:
                    await ReadDbShopService().set_delivery_options(
                        shop_id=data.id,
                        delivery_list=[make_serializable(dl) for dl in delivery_list]
                    )
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
                from infras.read_db.services.shop_service import ReadDbShopService
                await ReadDbShopService(conditions={"id": data.shop_id}).delete()
            except Exception as e:
                ic(f"Failed to sync shop deletion to MongoDB: {e}")
        return res


    

    async def get(self,data:GetAllShopsSchema)-> List[dict] | list:
        try:
            from infras.read_db.services.shop_service import ReadDbShopService
            read_service = ReadDbShopService(payload=None, conditions={})
            res = await read_service.get(query=data.query, limit=data.limit, offset=data.offset, visible_online=data.visible_online)
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
            from infras.read_db.services.shop_service import ReadDbShopService
            read_service = ReadDbShopService(payload=None, conditions={"id": data.shop_id})
            res = await read_service.get_one(queries={"id": data.shop_id})
        except Exception as e:
            ic(f"Failed to fetch shop from MongoDB: {e}")
            res = None

        if not res:
            res=await self.shop_repo_obj.get_shop_with_relations(shop_id=data.shop_id)
            if not res:
                res=await self.shop_repo_obj.getby_id(data=data)
                if res:
                    res = dict(res)
                    cats = res.get('categories', [])
                    res['category'] = cats[0] if cats else ''
                    res['datas'] = res.pop('additional_infos', {}) or {}
                    res['image_urls'] = []
        if res:
            add_infos = res.get('additional_infos') or res.get('datas') or {}
            vis_only = res.get('visibility_only', add_infos.get('visibility_only', False))
            res['visibility_only'] = bool(vis_only)
            res['is_ordering_enabled'] = bool(res.get('is_ordering_enabled', add_infos.get('is_ordering_enabled', not vis_only)))
            if vis_only:
                res['is_ordering_enabled'] = False
            hours = res.get("operating_hours") or []
            deliv = res.get("delivery_options") or []
            vis_online = bool(res.get("visible_online", False))
            has_hours = len(hours) > 0
            has_deliv = len(deliv) > 0
            res['has_operating_hours'] = has_hours
            res['has_delivery_options'] = has_deliv
            res['is_digital_store_configured'] = bool(has_hours or has_deliv or vis_online)
            res['can_show_digital_store_dashboard'] = bool(has_hours or has_deliv or vis_online)
        return res
    
    
    async def getby_userid(self,data:GetShopByUserIdSchema)-> List[dict] | list:
        try:
            from infras.read_db.services.shop_service import ReadDbShopService
            from infras.read_db.services.employee_service import ReadDbEmployeeService
            
            read_service = ReadDbShopService(payload=None, conditions={})
            owned_shops = await read_service.getby_queries(queries={"user_id": data.user_id}) or []
            
            emp_read_service = ReadDbEmployeeService(payload=None, conditions={})
            employees = await emp_read_service.getby_queries(queries={"user_id": data.user_id, "accepted": True}) or []
            emp_shop_ids = [emp.get("shop_id") for emp in employees if emp.get("shop_id")]
            
            emp_shops = []
            if emp_shop_ids:
                emp_shops = await read_service.getby_queries(queries={"id": {"$in": emp_shop_ids}}) or []
                
            res_dict = {shop.get("id"): shop for shop in owned_shops + emp_shops if shop.get("id")}
            res = list(res_dict.values())
            if not res and not owned_shops and not employees:
                res = None
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
                    r['datas'] = r.get('additional_infos', {}) or {}
                    r['image_urls'] = []
        if res:
            for r in res:
                add_infos = r.get('additional_infos') or r.get('datas') or {}
                vis_only = r.get('visibility_only', add_infos.get('visibility_only', False))
                r['visibility_only'] = bool(vis_only)
                r['is_ordering_enabled'] = bool(r.get('is_ordering_enabled', add_infos.get('is_ordering_enabled', not vis_only)))
                if vis_only:
                    r['is_ordering_enabled'] = False
                hours = r.get("operating_hours") or []
                deliv = r.get("delivery_options") or []
                vis_online = bool(r.get("visible_online", False))
                has_hours = len(hours) > 0
                has_deliv = len(deliv) > 0
                r['has_operating_hours'] = has_hours
                r['has_delivery_options'] = has_deliv
                r['is_digital_store_configured'] = bool(has_hours or has_deliv or vis_online)
                r['can_show_digital_store_dashboard'] = bool(has_hours or has_deliv or vis_online)
        return res

    async def get_bulk_by_ids(self, data: GetBulkShopsByIdSchema) -> List[dict]:
        try:
            from infras.read_db.services.shop_service import ReadDbShopService
            read_service = ReadDbShopService(payload=None, conditions={})
            res = await read_service.getby_queries(queries={"id": {"$in": data.shop_ids}})
        except Exception as e:
            ic(f"Failed to fetch bulk shops from MongoDB: {e}")
            res = None

        if not res:
            res = await self.shop_repo_obj.get_bulk_shops_by_id(shop_ids=data.shop_ids, timezone_val=data.timezone.value)
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
                from infras.read_db.services.shop_service import ReadDbShopService
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
                from infras.read_db.services.shop_service import ReadDbShopService
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
                from infras.read_db.services.shop_service import ReadDbShopService
                await ReadDbShopService().delete_operating_hours(hours_id=hours_id)
            except Exception as e:
                ic(f"Failed to sync operating hours deletion to MongoDB: {e}")
        return res

    # --- Delivery Options Service ---
    async def add_delivery_options(self, shop_id: str, data: CreateDeliverySchema) -> dict | None:
        res = await self.shop_repo_obj.add_delivery_options(shop_id=shop_id, data=data)
        if res:
            try:
                from infras.read_db.services.shop_service import ReadDbShopService
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
                from infras.read_db.services.shop_service import ReadDbShopService
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
                from infras.read_db.services.shop_service import ReadDbShopService
                await ReadDbShopService().delete_delivery_options(delivery_id=delivery_id)
            except Exception as e:
                ic(f"Failed to sync delivery options deletion to MongoDB: {e}")
        return res

    # --- Announcements Service ---
    async def add_announcement(self, shop_id: str, data: CreateAnnouncementSchema) -> dict | None:
        res = await self.shop_repo_obj.add_announcement(shop_id=shop_id, data=data)
        if res:
            try:
                from infras.read_db.services.shop_service import ReadDbShopService
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
                from infras.read_db.services.shop_service import ReadDbShopService
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
                from infras.read_db.services.shop_service import ReadDbShopService
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
        res = await self.shop_repo_obj.get_shop_followers(shop_id=shop_id) or []
        try:
            from infras.read_db.main import MONGO_CLIENT
            favs_coll = MONGO_CLIENT["DigitalStoreUserServiceDb"]["favourite_shops"]
            cursor = favs_coll.find({"shop_id": shop_id}, {"_id": 0, "user_id": 1})
            mongo_users = await cursor.to_list(length=1000)
            mongo_user_ids = [m["user_id"] for m in mongo_users if "user_id" in m]
            
            combined = list(dict.fromkeys(res + mongo_user_ids))
            return combined
        except Exception as e:
            ic(f"Error checking MongoDB followers: {e}")
            return res

    async def get_user_followed_shops(self, user_id: str) -> List[dict]:
        res = await self.shop_repo_obj.get_user_followed_shops(user_id=user_id)
        return res

    async def get_bulk_by_ids(self, data: GetBulkShopsByIdSchema) -> List[dict]:
        res = await self.shop_repo_obj.get_bulk_shops_by_id(shop_ids=data.shop_ids, timezone_val=data.timezone.value)
        return res

    async def get_geofenced_shops(self, data: GetGeofencedShopsSchema) -> List[dict]:
        try:
            from infras.read_db.services.shop_service import ReadDbShopService
            read_service = ReadDbShopService(payload=None, conditions={})
            shops = await read_service.getby_queries(queries={"visible_online": True})
        except Exception as e:
            ic(f"Failed to fetch geofenced shops from MongoDB: {e}")
            shops = None

        if not shops:
            shops = await self.shop_repo_obj.get_all_online_shops()
            if not shops:
                shops = await self.shop_repo_obj.get_geofenced_shops(data=data)
        
        def haversine(lat1, lon1, lat2, lon2):
            R = 6371.0
            dlat = math.radians(lat2 - lat1)
            dlon = math.radians(lon2 - lon1)
            a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
            return R * c
            
        default_radius_map = {
            "PICKUP_ONLY": 25.0,
            "INSTANT": 25.0,
            "STANDARD": 300.0,
            "NATIONWIDE": float('inf')
        }
        
        target_deliv_type = data.delivery_type.value.upper()
        is_nationwide = (target_deliv_type == "NATIONWIDE")
        
        try:
            user_lat = float(data.latitude)
            user_lon = float(data.longitude)
        except (ValueError, TypeError):
            return []

        filtered_shops = []
        for shop in shops:
            if not shop:
                continue
            
            # Check shop online visibility
            if not shop.get("visible_online"):
                continue
                
            delivery_options = shop.get("delivery_options") or []
            matched_delivery = None
            for d in delivery_options:
                if not d:
                    continue
                d_type = (d.get("type") or "").upper()
                d_enabled = d.get("enabled")
                if d_type == target_deliv_type and d_enabled is not False:
                    matched_delivery = d
                    break
                    
            if not matched_delivery:
                continue
                
            # Extract shop coordinates safely
            address = shop.get("address") or {}
            shop_lat_raw = address.get("latitude") if address.get("latitude") is not None else address.get("lat")
            shop_lon_raw = address.get("longitude") if address.get("longitude") is not None else address.get("lng")
            
            shop_lat = None
            shop_lon = None
            if shop_lat_raw is not None and shop_lon_raw is not None:
                try:
                    shop_lat = float(shop_lat_raw)
                    shop_lon = float(shop_lon_raw)
                except (ValueError, TypeError):
                    pass

            shop_copy = dict(shop)
            # Ensure resolved visibility_only and is_ordering_enabled
            add_infos = shop_copy.get("additional_infos") or shop_copy.get("datas") or {}
            vis_only = shop_copy.get("visibility_only", add_infos.get("visibility_only", False))
            shop_copy["visibility_only"] = bool(vis_only)
            shop_copy["is_ordering_enabled"] = bool(shop_copy.get("is_ordering_enabled", add_infos.get("is_ordering_enabled", not vis_only)))
            if vis_only:
                shop_copy["is_ordering_enabled"] = False
                
            cats = shop_copy.get("categories") or []
            shop_copy["category"] = cats[0] if cats else ""

            if is_nationwide:
                # Nationwide delivery matches regardless of distance
                if shop_lat is not None and shop_lon is not None:
                    dist = haversine(user_lat, user_lon, shop_lat, shop_lon)
                    shop_copy["distance_km"] = round(dist, 2)
                else:
                    shop_copy["distance_km"] = 0.0
                filtered_shops.append(shop_copy)
            else:
                # Distance-based delivery
                if shop_lat is None or shop_lon is None:
                    continue
                    
                dist = haversine(user_lat, user_lon, shop_lat, shop_lon)
                
                # Check shop's configured radius for this delivery option
                configured_radius = None
                raw_radius = matched_delivery.get("radius")
                if raw_radius is not None:
                    try:
                        configured_radius = float(raw_radius)
                    except (ValueError, TypeError):
                        pass
                
                if configured_radius is not None and configured_radius > 0:
                    max_radius = configured_radius
                else:
                    max_radius = default_radius_map.get(target_deliv_type, 25.0)
                    
                if dist <= max_radius:
                    shop_copy["distance_km"] = round(dist, 2)
                    filtered_shops.append(shop_copy)
                    
        # Sort by distance (closest first)
        filtered_shops.sort(key=lambda s: s.get("distance_km", 0.0))
        
        start_idx = (data.offset - 1) * data.limit
        end_idx = start_idx + data.limit
        return filtered_shops[start_idx:end_idx]

