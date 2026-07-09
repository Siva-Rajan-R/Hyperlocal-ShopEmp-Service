from pydantic import BaseModel, Field
from core.data_formats.enums.shop_enums import DeliveryTypeEnum, DeliveryByEnum
from typing import Optional

class CreateDeliverySchema(BaseModel):
    type: DeliveryTypeEnum
    speed: str
    free_shipping_amount: float
    delivery_by: DeliveryByEnum

class UpdateDeliverySchema(BaseModel):
    id: int
    type: Optional[DeliveryTypeEnum] = None
    speed: Optional[str] = None
    free_shipping_amount: Optional[float] = None
    delivery_by: Optional[DeliveryByEnum] = None
