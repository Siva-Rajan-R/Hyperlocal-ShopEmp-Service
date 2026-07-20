from ..repos.base_repo import ReadDbBaseRepo
from ..models.shop_model import ReadDbShopCreateModel, ReadDbShopReadModel, ReadDbShopUpdateModel
from ..main import SHOPS_COLLECTION
from typing import Optional, List, Any
from models.infra_models.readdb_model import BaseReadDbModel

class ReadDbShopService(BaseReadDbModel):
    def __init__(self, payload: Any = None, conditions: dict = None):
        self.payload = payload
        self.conditions = conditions or {}
        self.collection = SHOPS_COLLECTION
        self.base_Repo_obj = ReadDbBaseRepo(collection=self.collection)

    async def create(self):
        if not isinstance(self.payload, ReadDbShopCreateModel):
            return False
        data = self.payload.model_dump(mode="json", exclude_unset=True)
        return (await self.base_Repo_obj.create(data=data)).acknowledged

    async def update(self):
        if not isinstance(self.payload, ReadDbShopUpdateModel):
            return False
        data = self.payload.model_dump(mode="json", exclude_unset=True, exclude_none=True)
        return await self.base_Repo_obj.update(data=data, conditions=self.conditions)

    async def delete(self):
        return await self.base_Repo_obj.delete(conditions=self.conditions)

    async def get(self, query: str, limit: Optional[int] = None, offset: Optional[int] = None, visible_online: Optional[bool] = None):
        query = query.strip()
        queries = {
            "$or": [
                {'id': {'$regex': query, '$options': 'i'}},
                {'name': {'$regex': query, '$options': 'i'}},
                {'description': {'$regex': query, '$options': 'i'}},
                {'tagline': {'$regex': query, '$options': 'i'}},
                {'categories': {'$regex': query, '$options': 'i'}},
            ]
        }
        if visible_online is not None:
            queries = {
                "$and": [
                    queries,
                    {"visible_online": visible_online}
                ]
            }
        return await self.base_Repo_obj.get(queries=queries, offset=offset, limit=limit)

    async def getby_queries(self, queries: dict, limit: Optional[int] = None, offset: Optional[int] = None):
        return await self.base_Repo_obj.get(queries=queries, limit=limit, offset=offset)

    async def get_one(self, queries: dict):
        return await self.base_Repo_obj.get_one(queries=queries)

    # --- Operating Hours Sub-resources ---
    async def add_operating_hours(self, shop_id: str, hours: dict):
        res = await self.collection.update_one(
            {"id": shop_id},
            {"$push": {"operating_hours": hours}}
        )
        return res.modified_count > 0

    async def update_operating_hours(self, hours_id: int, hours: dict):
        # We need to set fields dynamically to avoid overwriting other keys or the id itself
        set_fields = {f"operating_hours.$.{k}": v for k, v in hours.items()}
        res = await self.collection.update_one(
            {"operating_hours.id": hours_id},
            {"$set": set_fields}
        )
        return res.modified_count > 0

    async def delete_operating_hours(self, hours_id: int):
        res = await self.collection.update_one(
            {"operating_hours.id": hours_id},
            {"$pull": {"operating_hours": {"id": hours_id}}}
        )
        return res.modified_count > 0

    # --- Delivery Options Sub-resources ---
    async def add_delivery_options(self, shop_id: str, delivery: dict):
        res = await self.collection.update_one(
            {"id": shop_id},
            {"$push": {"delivery_options": delivery}}
        )
        return res.modified_count > 0

    async def update_delivery_options(self, delivery_id: int, delivery: dict):
        set_fields = {f"delivery_options.$.{k}": v for k, v in delivery.items()}
        res = await self.collection.update_one(
            {"delivery_options.id": delivery_id},
            {"$set": set_fields}
        )
        return res.modified_count > 0

    async def delete_delivery_options(self, delivery_id: int):
        res = await self.collection.update_one(
            {"delivery_options.id": delivery_id},
            {"$pull": {"delivery_options": {"id": delivery_id}}}
        )
        return res.modified_count > 0

    # --- Announcements Sub-resources ---
    async def add_announcement(self, shop_id: str, announcement: dict):
        res = await self.collection.update_one(
            {"id": shop_id},
            {"$push": {"announcements": announcement}}
        )
        return res.modified_count > 0

    async def update_announcement(self, announcement_id: int, announcement: dict):
        set_fields = {f"announcements.$.{k}": v for k, v in announcement.items()}
        res = await self.collection.update_one(
            {"announcements.id": announcement_id},
            {"$set": set_fields}
        )
        return res.modified_count > 0

    async def delete_announcement(self, announcement_id: int):
        res = await self.collection.update_one(
            {"announcements.id": announcement_id},
            {"$pull": {"announcements": {"id": announcement_id}}}
        )
        return res.modified_count > 0
