from pydantic import BaseModel
from typing import List,Optional,Any
from core.data_formats.typ_dict.shop_typdict import ShopAddressTypDict,ShopBusinessInfoTypDict
from datetime import datetime


class ShopCreateResponseSchema(BaseModel):
    id:str
    user_id:str
    name:str
    ui_id:int
    category:str
    address:ShopAddressTypDict
    business_infos:ShopBusinessInfoTypDict
    datas:dict={}
    image_urls:list=[]
    visible_online:bool
    created_at:datetime
    updated_at:datetime

class ShopUpdateResponseSchema(BaseModel):
    id:str
    user_id:str
    name:str
    ui_id:int
    category:str
    business_infos:ShopBusinessInfoTypDict
    address:ShopAddressTypDict
    datas:dict={}
    image_urls:list=[]
    visible_online:bool
    created_at:datetime


class ShopDeleteResponseSchema(BaseModel):
    id:str
    user_id:str
    name:str
    ui_id:int
    category:str
    business_infos:ShopBusinessInfoTypDict
    address:ShopAddressTypDict
    datas:dict={}
    image_urls:list=[]
    visible_online:bool
    created_at:datetime


class ShopGetResponseSchema(BaseModel):
    id:str
    user_id:str
    name:str
    ui_id:int
    category:str
    business_infos:ShopBusinessInfoTypDict
    address:ShopAddressTypDict
    datas:dict={}
    image_urls:list=[]
    visible_online:bool
    created_at:datetime
    updated_at:datetime


class OperatingHoursResponseSchema(BaseModel):
    id: int
    shop_id: str
    open_at: Any
    close_at: Any
    day: str

class DeliveryResponseSchema(BaseModel):
    id: int
    shop_id: str
    type: str
    speed: Optional[str] = ""
    free_shipping_amount: Optional[float] = 0.0
    min_order_amount: Optional[float] = 0.0
    delivery_charge: Optional[float] = 0.0
    charge_per_km: Optional[float] = 0.0
    radius: Optional[float] = 0.0
    delivery_by: Optional[str] = "PARTNERS"
    enabled: Optional[bool] = True

class AnnouncementResponseSchema(BaseModel):
    id: int
    shop_id: str
    type: str
    message: str
    call_to_action: Optional[str] = None
    schedule_at: Optional[datetime] = None
    expire_at: Optional[datetime] = None
    send_to: str
    status: str
    created_at: datetime
    updated_at: datetime