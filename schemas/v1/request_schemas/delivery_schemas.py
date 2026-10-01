from pydantic import BaseModel, Field
from core.data_formats.enums.shop_enums import DeliveryTypeEnum, DeliveryByEnum
from typing import Optional

class CreateDeliverySchema(BaseModel):
    type: DeliveryTypeEnum
    speed: Optional[str] = ""
    free_shipping_amount: Optional[float] = 0.0
    min_order_amount: Optional[float] = 0.0
    delivery_charge: Optional[float] = 0.0
    charge_per_km: Optional[float] = 0.0
    radius: Optional[float] = 0.0
    base_distance: Optional[float] = 0.0
    extra_distance_step: Optional[float] = 1.0
    pricing_model: Optional[str] = "FLAT"
    delivery_by: Optional[DeliveryByEnum] = DeliveryByEnum.PARTNERS
    enabled: Optional[bool] = True

class UpdateDeliverySchema(BaseModel):
    id: Optional[int] = None
    type: Optional[DeliveryTypeEnum] = None
    speed: Optional[str] = None
    free_shipping_amount: Optional[float] = None
    min_order_amount: Optional[float] = None
    delivery_charge: Optional[float] = None
    charge_per_km: Optional[float] = None
    radius: Optional[float] = None
    base_distance: Optional[float] = None
    extra_distance_step: Optional[float] = None
    pricing_model: Optional[str] = None
    delivery_by: Optional[DeliveryByEnum] = None
    enabled: Optional[bool] = None
