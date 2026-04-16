from models.messaging_models.consumer_model import BaseConsumerModel
from hyperlocal_platform.core.typed_dicts.messaging_typdict import SuccessMessagingTypDict,EventPublishingTypDict
from hyperlocal_platform.core.enums.routingkey_enum import RoutingkeyActions,RoutingkeyState,RoutingkeyVersions
from core.errors.messaging_errors import ErrorTypeSEnum,BussinessError,FatalError,RetryableError,SagaStateErrorTypDict
from infras.primary_db.services.shop_service import ShopService
from infras.primary_db.main import AsyncShopEmployeeLocalSession
from hyperlocal_platform.core.enums.timezone_enum import TimeZoneEnum
from hyperlocal_platform.core.utils.routingkey_builder import generate_routingkey
from icecream import ic


class InventoryConsumer(BaseConsumerModel):
    async def create(self)->SuccessMessagingTypDict:
        event_data:dict=self.payload.get('data',{})
        inventory_data:dict=event_data.get('inventory')

        if not inventory_data:
            raise BussinessError(
                type=ErrorTypeSEnum.BUSSINESS_ERROR,
                error=SagaStateErrorTypDict(
                    code=ErrorTypeSEnum.BUSSINESS_ERROR,
                    debug="There is no inventory data present on the saga state payload",
                    user_msg="Invalid user data"
                )
            )
        async with AsyncShopEmployeeLocalSession() as session:
            shop_data=await ShopService(session=session).getby_id(shop_id=inventory_data['shop_id'],timezone=TimeZoneEnum.Asia_Kolkata)
            if not shop_data:
                raise BussinessError(
                    type=ErrorTypeSEnum.BUSSINESS_ERROR,
                    error=SagaStateErrorTypDict(
                        code=ErrorTypeSEnum.BUSSINESS_ERROR,
                        debug=f"There is no shop data matching for the shop id of {inventory_data['shop_id']}",
                        user_msg="Invalid shop id"
                    )
                )
        shop_data=shop_data.model_dump(mode='json')
        ic(shop_data,type(shop_data['address']))
        return SuccessMessagingTypDict(
            response=shop_data,
            set_response=True,
            emit_success=True,
            emit_payload=EventPublishingTypDict(
                exchange_name="shops.inventory.products.exchange",
                routing_key=generate_routingkey(
                    domain='shops',
                    work_for='inventory',
                    action=RoutingkeyActions.CREATE,
                    state=RoutingkeyState.REQUESTED,
                    version=RoutingkeyVersions.V1
                ),
                payload={},
                headers=self.headers
            )
        )
    
    async def update(self):
        res:SuccessMessagingTypDict=await self.create()
        res['emit_payload']['routing_key']=generate_routingkey(
            domain='shops',
            work_for='inventory',
            action=RoutingkeyActions.UPDATE,
            state=RoutingkeyState.REQUESTED,
            version=RoutingkeyVersions.V1
        )
        return res
    
    async def delete(self):
        ...