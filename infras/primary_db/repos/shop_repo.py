from infras.primary_db.models.shop_model import Shops, ShopOperatingHours, ShopDelivery, ShopAnnouncements, ShopFollowers
from sqlalchemy import select,update,delete,or_,and_,func,String
from sqlalchemy.dialects.postgresql import insert
from schemas.v1.db_schemas.shop_schemas import CreateShopDbSchema,UpdateShopDbSchema,DeleteShopDbSchema
from schemas.v1.request_schemas.shop_schemas import GetAllShopsSchema,GetShopByIdSchema,GetShopByUserIdSchema,VerifyShoSchema
from schemas.v1.request_schemas.operating_hours_schemas import CreateOperatingHoursSchema, UpdateOperatingHoursSchema
from schemas.v1.request_schemas.delivery_schemas import CreateDeliverySchema, UpdateDeliverySchema
from schemas.v1.request_schemas.announcement_schemas import CreateAnnouncementSchema, UpdateAnnouncementSchema
from models.repo_models.base_repo_model import BaseRepoModel
from hyperlocal_platform.core.decorators.db_session_handler_dec import start_db_transaction
from core.decorators.error_handler_dec import catch_errors
from hyperlocal_platform.core.models.req_res_models import SuccessResponseTypDict,ErrorResponseTypDict,BaseResponseTypDict
from infras.primary_db.models.employee_model import Employees
from fastapi.exceptions import HTTPException
from hyperlocal_platform.core.enums.timezone_enum import TimeZoneEnum
from sqlalchemy.ext.asyncio import AsyncSession
from icecream import ic
from typing import List,Optional

def _serialize_shop_model(shop: Shops) -> Optional[dict]:
    if not shop:
        return None
    cats = shop.categories or []
    add_infos = shop.additional_infos or {}
    if not isinstance(add_infos, dict):
        add_infos = {}
    vis_only = add_infos.get("visibility_only", False)
    ord_enabled = add_infos.get("is_ordering_enabled", not vis_only)
    if vis_only:
        ord_enabled = False

    hours_list = []
    if getattr(shop, "operating_hours", None):
        for hr in shop.operating_hours:
            hours_list.append({
                "id": hr.id,
                "shop_id": hr.shop_id,
                "open_at": str(hr.open_at),
                "close_at": str(hr.close_at),
                "day": hr.day
            })

    delivery_list = []
    if getattr(shop, "delivery_options", None):
        for deliv in shop.delivery_options:
            delivery_list.append({
                "id": deliv.id,
                "shop_id": deliv.shop_id,
                "type": deliv.type,
                "speed": deliv.speed,
                "free_shipping_amount": deliv.free_shipping_amount,
                "min_order_amount": deliv.min_order_amount,
                "delivery_charge": deliv.delivery_charge,
                "charge_per_km": deliv.charge_per_km,
                "radius": deliv.radius,
                "delivery_by": deliv.delivery_by,
                "enabled": deliv.enabled
            })

    announcements_list = []
    if getattr(shop, "announcements", None):
        for ann in shop.announcements:
            announcements_list.append({
                "id": ann.id,
                "shop_id": ann.shop_id,
                "type": ann.type,
                "message": ann.message,
                "call_to_action": ann.call_to_action,
                "schedule_at": ann.schedule_at.isoformat() if ann.schedule_at else None,
                "expire_at": ann.expire_at.isoformat() if ann.expire_at else None,
                "send_to": ann.send_to,
                "status": ann.status
            })

    has_hours = len(hours_list) > 0
    has_deliv = len(delivery_list) > 0
    is_ds_configured = bool(has_hours or has_deliv or shop.visible_online)

    return {
        "id": shop.id,
        "ui_id": shop.ui_id,
        "sequence_id": shop.sequence_id,
        "user_id": shop.user_id,
        "name": shop.name,
        "description": shop.description,
        "tagline": shop.tagline,
        "categories": cats,
        "category": cats[0] if cats else "",
        "business_infos": shop.business_infos or {},
        "address": shop.address or {},
        "banner_url": shop.banner_url,
        "logo_url": shop.logo_url,
        "additional_infos": add_infos,
        "datas": add_infos,
        "visible_online": shop.visible_online,
        "visibility_only": vis_only,
        "is_ordering_enabled": ord_enabled,
        "has_operating_hours": has_hours,
        "has_delivery_options": has_deliv,
        "is_digital_store_configured": is_ds_configured,
        "can_show_digital_store_dashboard": is_ds_configured,
        "image_urls": [],
        "operating_hours": hours_list,
        "delivery_options": delivery_list,
        "announcements": announcements_list,
        "created_at": shop.created_at.isoformat() if hasattr(shop.created_at, "isoformat") else str(shop.created_at),
        "updated_at": shop.updated_at.isoformat() if hasattr(shop.updated_at, "isoformat") else str(shop.updated_at),
    }

def _map_shop(row) -> Optional[dict]:
    if not row:
        return None
    d = dict(row)
    # Map model to schema fields
    cats = d.pop('categories', [])
    d['category'] = cats[0] if cats else ''
    add_infos = d.pop('additional_infos', {}) or {}
    d['datas'] = add_infos
    d['additional_infos'] = add_infos
    vis_only = add_infos.get("visibility_only", False) if isinstance(add_infos, dict) else False
    ord_enabled = add_infos.get("is_ordering_enabled", not vis_only) if isinstance(add_infos, dict) else True
    if vis_only:
        ord_enabled = False
    d['visibility_only'] = vis_only
    d['is_ordering_enabled'] = ord_enabled
    vis_online = bool(d.get("visible_online", False))
    d['has_operating_hours'] = False
    d['has_delivery_options'] = False
    d['is_digital_store_configured'] = vis_online
    d['can_show_digital_store_dashboard'] = vis_online
    d['image_urls'] = []
    return d

class ShopRepo(BaseRepoModel):
    def __init__(self, session:AsyncSession):
        super().__init__(session)
        self.shop_cols=(
            Shops.id,
            Shops.user_id,
            Shops.sequence_id,
            Shops.name,
            Shops.description,
            Shops.tagline,
            Shops.categories,
            Shops.business_infos,
            Shops.address,
            Shops.banner_url,
            Shops.logo_url,
            Shops.additional_infos,
            Shops.visible_online,
            Shops.updated_at,
            Shops.created_at,
            Shops.ui_id
        )


    async def is_shop_exists(self,user_or_shop_id:str):
        # Checks if shop exists by shop_id or by user_id
        stmt = (
            select(Shops.id)
            .where(
                or_(
                    Shops.id==user_or_shop_id,
                    Shops.user_id==user_or_shop_id
                )
            )
            .limit(1)
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()
    

    @start_db_transaction
    async def create(self, data:CreateShopDbSchema)->dict | None:
        values = data.model_dump(mode="json")

        stmt = (
            insert(Shops)
            .values(**values)
            .returning(*self.shop_cols)
        )

        shop=(await self.session.execute(stmt)).mappings().one_or_none()
        return shop
    

    @start_db_transaction
    async def update(self, data:UpdateShopDbSchema)-> dict | None:
        data_toupdate=data.model_dump(mode="json",exclude=['id','user_id'],exclude_unset=True,exclude_none=True)
        # Map schema to model fields
        if 'category' in data_toupdate:
            data_toupdate['categories'] = data_toupdate.pop('category')
        if 'datas' in data_toupdate:
            data_toupdate['additional_infos'] = data_toupdate.pop('datas')
        if 'image_urls' in data_toupdate:
            data_toupdate.pop('image_urls')



        shop_toupdate=(
            update(Shops)
            .where(
                Shops.id==data.id,
                Shops.user_id==data.user_id
            )
            .values(**data_toupdate)
        ).returning(
            *self.shop_cols
        )

        is_updated=(await self.session.execute(shop_toupdate)).mappings().one_or_none()
        return is_updated
    

    @start_db_transaction
    async def delete(self,data:DeleteShopDbSchema)-> dict | None:
        shop_todel=(
            delete(Shops)
            .where(
                Shops.id==data.shop_id,
                Shops.user_id==data.user_id
            )
        ).returning(
            *self.shop_cols
        )

        is_deleted=(await self.session.execute(shop_todel)).mappings().one_or_none()
        return is_deleted
    

    async def get(self,data:GetAllShopsSchema)-> List[dict] | list:
        search_term=f"%{data.query}%"
        cursor=(data.offset-1)*data.limit
        created_at=func.date(func.timezone(data.timezone.value,Shops.created_at)).label("created_at")

        where_conds = [
            or_(
                Shops.id.ilike(search_term),
                func.cast(created_at,String).ilike(search_term)
            ),
            Shops.sequence_id>cursor
        ]
        if data.visible_online is not None:
            where_conds.append(Shops.visible_online == data.visible_online)

        shop_stmt=(
            select(
                *self.shop_cols,
                created_at,
            )
            .where(
                and_(*where_conds)
            )
            .order_by(Shops.created_at.desc())
            .limit(limit=data.limit)
            .offset(offset=cursor)
        )

        shops=(await self.session.execute(shop_stmt)).mappings().all()
        return shops
    

    async def getby_id(self,data:GetShopByIdSchema)-> dict | None:
        created_at=func.date(func.timezone(data.timezone.value,Shops.created_at)).label("created_at")

        shop_stmt=(
            select(
                *self.shop_cols,
                created_at,
            )
            .where(
                Shops.id==data.shop_id
            )
        )

        shop=(await self.session.execute(shop_stmt)).mappings().one_or_none()
        return shop
    
    

    async def getby_userid(self,data:GetShopByUserIdSchema)-> List[dict] | list:
        # Shops owned by the user
        stmt1 = select(Shops).where(Shops.user_id == data.user_id)
        res1 = await self.session.execute(stmt1)
        owned_shops = res1.scalars().all()

        # Shops where the user is an employee
        stmt2 = select(Shops).join(Employees, Employees.shop_id == Shops.id).where(
            and_(
                Employees.user_id == data.user_id,
                Employees.accepted == True
            )
        )
        res2 = await self.session.execute(stmt2)
        emp_shops = res2.scalars().all()

        all_shops_map = {}
        for s in list(owned_shops) + list(emp_shops):
            if s and s.id not in all_shops_map:
                all_shops_map[s.id] = _serialize_shop_model(s)
        return list(all_shops_map.values())
    

    async def verify_shop(self,data:VerifyShoSchema)-> dict | None:
        stmt=(
            select(
                Shops.id
            )
            .where(
                Shops.id==data.shop_id
            )
        )

        result=(await self.session.execute(stmt)).scalar_one_or_none()

        if result:
            return {"id":result,'exists':True}
        
        return {"id":'','exists':False}
    
    

    async def search(self,data:GetAllShopsSchema)-> List[dict] | list:
        search_term=f"%{data.query}%"

        shop_stmt=(
            select(
                Shops.id,
                Shops.additional_infos.label("datas")
            )
            .where(
                or_(
                    Shops.id.ilike(search_term)
                )
            )
            .limit(limit=data.limit)
        )

        shop=(await self.session.execute(shop_stmt)).mappings().all()
        return shop

    # --- Operating Hours CRUD ---
    @start_db_transaction
    async def add_operating_hours(self, shop_id: str, data: CreateOperatingHoursSchema) -> dict | None:
        # Check if operating hours for this day already exists
        check_stmt = select(ShopOperatingHours).where(
            and_(
                ShopOperatingHours.shop_id == shop_id,
                ShopOperatingHours.day == data.day
            )
        )
        existing = (await self.session.execute(check_stmt)).scalar_one_or_none()
        if existing:
            existing.open_at = data.open_at
            existing.close_at = data.close_at
            await self.session.flush()
            return {
                "id": existing.id,
                "shop_id": existing.shop_id,
                "open_at": existing.open_at,
                "close_at": existing.close_at,
                "day": existing.day
            }

        values = data.model_dump()
        values["shop_id"] = shop_id
        stmt = insert(ShopOperatingHours).values(**values).returning(
            ShopOperatingHours.id,
            ShopOperatingHours.shop_id,
            ShopOperatingHours.open_at,
            ShopOperatingHours.close_at,
            ShopOperatingHours.day
        )
        res = (await self.session.execute(stmt)).mappings().one_or_none()
        return res

    async def get_operating_hours(self, shop_id: str) -> List[dict]:
        stmt = select(
            ShopOperatingHours.id,
            ShopOperatingHours.shop_id,
            ShopOperatingHours.open_at,
            ShopOperatingHours.close_at,
            ShopOperatingHours.day
        ).where(ShopOperatingHours.shop_id == shop_id)
        res = (await self.session.execute(stmt)).mappings().all()
        return res

    @start_db_transaction
    async def update_operating_hours(self, hours_id: int, data: UpdateOperatingHoursSchema) -> dict | None:
        values = data.model_dump(exclude={"id"}, exclude_unset=True, exclude_none=True)
        stmt = update(ShopOperatingHours).where(ShopOperatingHours.id == hours_id).values(**values).returning(
            ShopOperatingHours.id,
            ShopOperatingHours.shop_id,
            ShopOperatingHours.open_at,
            ShopOperatingHours.close_at,
            ShopOperatingHours.day
        )
        res = (await self.session.execute(stmt)).mappings().one_or_none()
        return res

    @start_db_transaction
    async def delete_operating_hours(self, hours_id: int) -> dict | None:
        stmt = delete(ShopOperatingHours).where(ShopOperatingHours.id == hours_id).returning(
            ShopOperatingHours.id,
            ShopOperatingHours.shop_id,
            ShopOperatingHours.open_at,
            ShopOperatingHours.close_at,
            ShopOperatingHours.day
        )
        res = (await self.session.execute(stmt)).mappings().one_or_none()
        return res

    # --- Delivery Options CRUD ---
    @start_db_transaction
    async def add_delivery_options(self, shop_id: str, data: CreateDeliverySchema) -> dict | None:
        deliv_type = data.type.value if hasattr(data.type, "value") else data.type
        # Check if delivery option for this type already exists
        check_stmt = select(ShopDelivery).where(
            and_(
                ShopDelivery.shop_id == shop_id,
                ShopDelivery.type == deliv_type
            )
        )
        existing = (await self.session.execute(check_stmt)).scalar_one_or_none()
        if existing:
            if data.speed is not None:
                existing.speed = data.speed
            if data.free_shipping_amount is not None:
                existing.free_shipping_amount = data.free_shipping_amount
            if data.min_order_amount is not None:
                existing.min_order_amount = data.min_order_amount
            if data.delivery_charge is not None:
                existing.delivery_charge = data.delivery_charge
            if data.charge_per_km is not None:
                existing.charge_per_km = data.charge_per_km
            if data.radius is not None:
                existing.radius = data.radius
            if data.delivery_by is not None:
                existing.delivery_by = data.delivery_by.value if hasattr(data.delivery_by, "value") else data.delivery_by
            if data.enabled is not None:
                existing.enabled = data.enabled
            await self.session.flush()
            return {
                "id": existing.id,
                "shop_id": existing.shop_id,
                "type": existing.type,
                "speed": existing.speed,
                "free_shipping_amount": existing.free_shipping_amount,
                "min_order_amount": existing.min_order_amount,
                "delivery_charge": existing.delivery_charge,
                "charge_per_km": existing.charge_per_km,
                "radius": existing.radius,
                "delivery_by": existing.delivery_by,
                "enabled": existing.enabled
            }

        values = data.model_dump(mode="json", exclude_none=True)
        values["shop_id"] = shop_id
        stmt = insert(ShopDelivery).values(**values).returning(
            ShopDelivery.id,
            ShopDelivery.shop_id,
            ShopDelivery.type,
            ShopDelivery.speed,
            ShopDelivery.free_shipping_amount,
            ShopDelivery.min_order_amount,
            ShopDelivery.delivery_charge,
            ShopDelivery.charge_per_km,
            ShopDelivery.radius,
            ShopDelivery.delivery_by,
            ShopDelivery.enabled
        )
        res = (await self.session.execute(stmt)).mappings().one_or_none()
        return res

    async def get_delivery_options(self, shop_id: str) -> List[dict]:
        stmt = select(
            ShopDelivery.id,
            ShopDelivery.shop_id,
            ShopDelivery.type,
            ShopDelivery.speed,
            ShopDelivery.free_shipping_amount,
            ShopDelivery.min_order_amount,
            ShopDelivery.delivery_charge,
            ShopDelivery.charge_per_km,
            ShopDelivery.radius,
            ShopDelivery.delivery_by,
            ShopDelivery.enabled
        ).where(ShopDelivery.shop_id == shop_id)
        res = (await self.session.execute(stmt)).mappings().all()
        return res

    @start_db_transaction
    async def update_delivery_options(self, delivery_id: int, data: UpdateDeliverySchema) -> dict | None:
        values = data.model_dump(mode="json", exclude={"id"}, exclude_unset=True, exclude_none=True)
        stmt = update(ShopDelivery).where(ShopDelivery.id == delivery_id).values(**values).returning(
            ShopDelivery.id,
            ShopDelivery.shop_id,
            ShopDelivery.type,
            ShopDelivery.speed,
            ShopDelivery.free_shipping_amount,
            ShopDelivery.min_order_amount,
            ShopDelivery.delivery_charge,
            ShopDelivery.charge_per_km,
            ShopDelivery.radius,
            ShopDelivery.delivery_by,
            ShopDelivery.enabled
        )
        res = (await self.session.execute(stmt)).mappings().one_or_none()
        return res

    @start_db_transaction
    async def delete_delivery_options(self, delivery_id: int) -> dict | None:
        stmt = delete(ShopDelivery).where(ShopDelivery.id == delivery_id).returning(
            ShopDelivery.id,
            ShopDelivery.shop_id,
            ShopDelivery.type,
            ShopDelivery.speed,
            ShopDelivery.free_shipping_amount,
            ShopDelivery.min_order_amount,
            ShopDelivery.delivery_charge,
            ShopDelivery.charge_per_km,
            ShopDelivery.radius,
            ShopDelivery.delivery_by,
            ShopDelivery.enabled
        )
        res = (await self.session.execute(stmt)).mappings().one_or_none()
        return res

    # --- Announcements CRUD ---
    @start_db_transaction
    async def add_announcement(self, shop_id: str, data: CreateAnnouncementSchema) -> dict | None:
        values = data.model_dump()
        values["shop_id"] = shop_id
        stmt = insert(ShopAnnouncements).values(**values).returning(
            ShopAnnouncements.id,
            ShopAnnouncements.shop_id,
            ShopAnnouncements.type,
            ShopAnnouncements.message,
            ShopAnnouncements.call_to_action,
            ShopAnnouncements.schedule_at,
            ShopAnnouncements.expire_at,
            ShopAnnouncements.send_to,
            ShopAnnouncements.status,
            ShopAnnouncements.created_at,
            ShopAnnouncements.updated_at
        )
        res = (await self.session.execute(stmt)).mappings().one_or_none()
        return res

    async def get_announcements(self, shop_id: str) -> List[dict]:
        stmt = select(
            ShopAnnouncements.id,
            ShopAnnouncements.shop_id,
            ShopAnnouncements.type,
            ShopAnnouncements.message,
            ShopAnnouncements.call_to_action,
            ShopAnnouncements.schedule_at,
            ShopAnnouncements.expire_at,
            ShopAnnouncements.send_to,
            ShopAnnouncements.status,
            ShopAnnouncements.created_at,
            ShopAnnouncements.updated_at
        ).where(ShopAnnouncements.shop_id == shop_id)
        res = (await self.session.execute(stmt)).mappings().all()
        return res

    @start_db_transaction
    async def update_announcement(self,data: UpdateAnnouncementSchema,shop_id:str) -> dict | None:
        values = data.model_dump(exclude={"id"}, exclude_unset=True, exclude_none=True)
        stmt = update(ShopAnnouncements).where(ShopAnnouncements.id == data.id,ShopAnnouncements.shop_id == shop_id).values(**values).returning(
            ShopAnnouncements.id,
            ShopAnnouncements.shop_id,
            ShopAnnouncements.type,
            ShopAnnouncements.message,
            ShopAnnouncements.call_to_action,
            ShopAnnouncements.schedule_at,
            ShopAnnouncements.expire_at,
            ShopAnnouncements.send_to,
            ShopAnnouncements.status,
            ShopAnnouncements.created_at,
            ShopAnnouncements.updated_at
        )
        res = (await self.session.execute(stmt)).mappings().one_or_none()
        return res


    @start_db_transaction
    async def delete_announcement(self, announcement_id: int,shop_id:str) -> dict | None:
        stmt = delete(ShopAnnouncements).where(ShopAnnouncements.id == announcement_id,ShopAnnouncements.shop_id==shop_id).returning(
            ShopAnnouncements.id,
            ShopAnnouncements.shop_id,
            ShopAnnouncements.type,
            ShopAnnouncements.message,
            ShopAnnouncements.call_to_action,
            ShopAnnouncements.schedule_at,
            ShopAnnouncements.expire_at,
            ShopAnnouncements.send_to,
            ShopAnnouncements.status,
            ShopAnnouncements.created_at,
            ShopAnnouncements.updated_at
        )
        res = (await self.session.execute(stmt)).mappings().one_or_none()
        return res

    # --- Validation Helpers ---
    async def count_operating_hours(self, shop_id: str) -> int:
        stmt = select(func.count(ShopOperatingHours.id)).where(ShopOperatingHours.shop_id == shop_id)
        return (await self.session.execute(stmt)).scalar() or 0

    async def count_delivery_options(self, shop_id: str) -> int:
        stmt = select(func.count(ShopDelivery.id)).where(ShopDelivery.shop_id == shop_id)
        return (await self.session.execute(stmt)).scalar() or 0

    async def is_shop_visible_online(self, shop_id: str) -> bool:
        stmt = select(Shops.visible_online).where(Shops.id == shop_id)
        res = (await self.session.execute(stmt)).scalar_one_or_none()
        return bool(res)

    async def get_shop_id_by_operating_hours_id(self, hours_id: int) -> str | None:
        stmt = select(ShopOperatingHours.shop_id).where(ShopOperatingHours.id == hours_id)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def get_shop_id_by_delivery_id(self, delivery_id: int) -> str | None:
        stmt = select(ShopDelivery.shop_id).where(ShopDelivery.id == delivery_id)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    @start_db_transaction
    async def follow_shop(self, shop_id: str, user_id: str) -> dict | None:
        check_stmt = select(ShopFollowers).where(
            and_(ShopFollowers.shop_id == shop_id, ShopFollowers.user_id == user_id)
        )
        existing = (await self.session.execute(check_stmt)).scalars().first()
        if existing:
            return {"id": existing.id, "shop_id": existing.shop_id, "user_id": existing.user_id}
        
        new_follow = ShopFollowers(shop_id=shop_id, user_id=user_id)
        self.session.add(new_follow)
        await self.session.flush()
        return {"id": new_follow.id, "shop_id": new_follow.shop_id, "user_id": new_follow.user_id}

    @start_db_transaction
    async def unfollow_shop(self, shop_id: str, user_id: str) -> bool:
        stmt = delete(ShopFollowers).where(
            and_(ShopFollowers.shop_id == shop_id, ShopFollowers.user_id == user_id)
        )
        res = await self.session.execute(stmt)
        return res.rowcount > 0

    async def get_shop_followers(self, shop_id: str) -> List[str]:
        stmt = select(ShopFollowers.user_id).where(ShopFollowers.shop_id == shop_id)
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def get_user_followed_shops(self, user_id: str) -> List[dict]:
        stmt = select(
            Shops.id, Shops.name, Shops.description, Shops.logo_url
        ).join(
            ShopFollowers, Shops.id == ShopFollowers.shop_id
        ).where(
            ShopFollowers.user_id == user_id
        )
        res = await self.session.execute(stmt)
        return [dict(r) for r in res.mappings().all()]

    async def get_bulk_shops_by_id(self, shop_ids: List[str], timezone_val: str) -> List[dict]:
        created_at = func.date(func.timezone(timezone_val, Shops.created_at)).label("created_at")
        stmt = select(
            *self.shop_cols,
            created_at
        ).where(
            Shops.id.in_(shop_ids)
        )
        res = await self.session.execute(stmt)
        return [_map_shop(row) for row in res.mappings().all()]

    async def get_all_online_shops(self) -> List[dict]:
        stmt = select(Shops).where(Shops.visible_online == True)
        res = await self.session.execute(stmt)
        shops = res.scalars().all()
        return [_serialize_shop_model(s) for s in shops if s]

    async def get_shop_with_relations(self, shop_id: str) -> Optional[dict]:
        stmt = select(Shops).where(Shops.id == shop_id)
        res = await self.session.execute(stmt)
        shop = res.scalar_one_or_none()
        return _serialize_shop_model(shop) if shop else None

    async def get_geofenced_shops(self, data) -> List[dict]:
        stmt = (
            select(Shops)
            .join(ShopDelivery, ShopDelivery.shop_id == Shops.id)
            .where(
                and_(
                    Shops.visible_online == True,
                    ShopDelivery.type == data.delivery_type.value,
                    or_(ShopDelivery.enabled == True, ShopDelivery.enabled == None)
                )
            )
            .distinct()
        )
        res = await self.session.execute(stmt)
        shops = res.scalars().all()
        return [_serialize_shop_model(s) for s in shops if s]





