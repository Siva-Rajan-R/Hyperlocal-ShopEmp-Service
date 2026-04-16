from pydantic import BaseModel
from core.data_formats.typ_dict.shop_typdict import ShopAddressTypDict
from core.data_formats.enums.shop_enums import ShopTypeEnum
from typing import Optional,Dict,Any


class CreateShopSchema(BaseModel):
    datas:Dict[str,Any]


class UpdateShopSchema(BaseModel):
    id:str
    datas:Optional[dict]=None