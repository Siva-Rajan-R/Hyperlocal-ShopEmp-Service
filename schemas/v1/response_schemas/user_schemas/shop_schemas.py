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
    created_at:datetime
    updated_at:datetime