from pydantic import BaseModel
from typing import List,Optional
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
    open_at: datetime
    close_at: datetime
    day: str

class DeliveryResponseSchema(BaseModel):
    id: int
    shop_id: str
    type: str
    speed: str
    free_shipping_amount: float
    delivery_by: str

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