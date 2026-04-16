from pydantic import BaseModel
from core.data_formats.typ_dict.shop_typdict import ShopAddressTypDict
from core.data_formats.enums.shop_enums import ShopTypeEnum
from typing import Optional


class CreateShopDbSchema(BaseModel):
    id:str
    account_id:str
    datas:dict


class UpdateShopDbSchema(BaseModel):
    id:str
    account_id:str
    datas:dict