from pydantic import BaseModel
from core.data_formats.typ_dict.shop_typdict import ShopAddressTypDict
from core.data_formats.enums.shop_enums import ShopTypeEnum
from typing import Optional

class ResponseShopSchema(BaseModel):
    id:str
    description:str
    address:ShopAddressTypDict
    gst_no:str
    is_verified:bool
    account_id:str
    mobile_number:str
    name:str
    type:ShopTypeEnum