from pydantic import BaseModel
from core.data_formats.typ_dict.shop_typdict import ShopAddressTypDict,ShopBusinessInfoTypDict
from core.data_formats.enums.shop_enums import ShopTypeEnum
from typing import Optional


class CreateShopDbSchema(BaseModel):
    id:str
    account_id:str
    name:str
    category:str
    address:ShopAddressTypDict
    business_infos:ShopBusinessInfoTypDict
    image_urls:Optional[list]=[]
    datas:Optional[dict]={}


class UpdateShopDbSchema(BaseModel):
    id:str
    account_id:str
    name:Optional[str]=None
    category:Optional[str]=None
    address:Optional[ShopAddressTypDict]=None
    business_infos:Optional[ShopBusinessInfoTypDict]=None
    image_urls:Optional[list]=[]
    datas:Optional[dict]={}

class DeleteShopDbSchema(BaseModel):
    shop_id:str
    account_id:str