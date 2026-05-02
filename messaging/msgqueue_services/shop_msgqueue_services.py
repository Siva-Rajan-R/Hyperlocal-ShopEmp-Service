from infras.primary_db.services.shop_service import ShopService
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.v1.response_schemas.msgqueue_schemas.shop_schemas import ShopUpdateResponseSchema,ShopCreateResponseSchema,ShopDeleteResponseSchema,ShopBusinessInfoTypDict,ShopGetResponseSchema
from schemas.v1.request_schemas.shop_schemas import CreateShopSchema,UpdateShopSchema,DeleteShopSchema,GetAllShopsSchema,GetShopByAccountIdSchema,GetShopByIdSchema,VerifyShoSchema
from typing import Union,List,Optional
from infras.primary_db.main import AsyncShopEmployeeLocalSession

class MessagingQueueShopService:
    
    async def verify_shop(self,data:Union[VerifyShoSchema,dict]):
        if isinstance(data, dict):
            data = VerifyShoSchema(**data)
        async with AsyncShopEmployeeLocalSession() as session:
            shop_service_obj=ShopService(session=session)
            res=await shop_service_obj.verify_shop(data=data)

            return res
        

    async def get_shops(self,data:Union[GetAllShopsSchema,dict]):
        if isinstance(data, dict):
            data = GetAllShopsSchema(**data)
        async with AsyncShopEmployeeLocalSession() as session:
            shop_service_obj=ShopService(session=session)
            res=await shop_service_obj.get(data=data)

            if not res:
                return res

            return [ShopGetResponseSchema(**r).model_dump(mode="json") for r in res]
    
    async def get_shop_by_id(self,data:Union[GetShopByIdSchema,dict]):
        if isinstance(data, dict):
            data = GetShopByIdSchema(**data)
        async with AsyncShopEmployeeLocalSession() as session:
            shop_service_obj=ShopService(session=session)
            res=await shop_service_obj.getby_id(data=data)

            if not res:
                return res
            
            return ShopGetResponseSchema(**res).model_dump(mode="json")
    
    async def get_shop_by_account_id(self,data:Union[GetShopByAccountIdSchema,dict]):
        if isinstance(data, dict):
            data = GetShopByAccountIdSchema(**data)
        async with AsyncShopEmployeeLocalSession() as session:
            shop_service_obj=ShopService(session=session)
            res=await shop_service_obj.getby_accountid(data=data)

            if not res:
                return res
            
            return [ShopGetResponseSchema(**r).model_dump(mode="json") for r in res]


    