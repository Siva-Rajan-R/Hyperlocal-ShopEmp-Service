from ..models.shop_model import Shops, ShopOperatingHours, ShopDelivery, ShopAnnouncements
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
from ..models.employee_model import Employees
from fastapi.exceptions import HTTPException
from hyperlocal_platform.core.enums.timezone_enum import TimeZoneEnum
from sqlalchemy.ext.asyncio import AsyncSession
from icecream import ic
from typing import List,Optional

def _map_shop(row) -> Optional[dict]:
    if not row:
        return None
    d = dict(row)
    # Map model to schema fields
    cats = d.pop('categories', [])
    d['category'] = cats[0] if cats else ''
    d['datas'] = d.pop('additional_infos', {}) or {}
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

        shop_stmt=(
            select(
                *self.shop_cols,
                created_at,
            )
            .where(
                and_(
                    or_(
                        Shops.id.ilike(search_term),
                        func.cast(created_at,String).ilike(search_term)
                    ),
                    Shops.sequence_id>cursor
                )
                
            )
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
        created_at=func.date(func.timezone(data.timezone.value,Shops.created_at)).label("created_at")
        shop_stmt=(
            select(
                *self.shop_cols,
                created_at
            )
            .where(
                Shops.user_id==data.user_id
            )
        )

        shops=(await self.session.execute(shop_stmt)).mappings().all()
        return shops
    

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
        values = data.model_dump()
        values["shop_id"] = shop_id
        stmt = insert(ShopDelivery).values(**values).returning(
            ShopDelivery.id,
            ShopDelivery.shop_id,
            ShopDelivery.type,
            ShopDelivery.speed,
            ShopDelivery.free_shipping_amount,
            ShopDelivery.delivery_by
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
            ShopDelivery.delivery_by
        ).where(ShopDelivery.shop_id == shop_id)
        res = (await self.session.execute(stmt)).mappings().all()
        return res

    @start_db_transaction
    async def update_delivery_options(self, delivery_id: int, data: UpdateDeliverySchema) -> dict | None:
        values = data.model_dump(exclude={"id"}, exclude_unset=True, exclude_none=True)
        stmt = update(ShopDelivery).where(ShopDelivery.id == delivery_id).values(**values).returning(
            ShopDelivery.id,
            ShopDelivery.shop_id,
            ShopDelivery.type,
            ShopDelivery.speed,
            ShopDelivery.free_shipping_amount,
            ShopDelivery.delivery_by
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
            ShopDelivery.delivery_by
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
    async def update_announcement(self, announcement_id: int, data: UpdateAnnouncementSchema) -> dict | None:
        values = data.model_dump(exclude={"id"}, exclude_unset=True, exclude_none=True)
        stmt = update(ShopAnnouncements).where(ShopAnnouncements.id == announcement_id).values(**values).returning(
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
    async def delete_announcement(self, announcement_id: int) -> dict | None:
        stmt = delete(ShopAnnouncements).where(ShopAnnouncements.id == announcement_id).returning(
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


