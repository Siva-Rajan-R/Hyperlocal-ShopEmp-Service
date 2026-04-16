from pydantic import BaseModel
from core.data_formats.typ_dict.shop_typdict import ShopAddressTypDict
from core.data_formats.enums.role_enums import RoleEnum
from typing import Optional

class CreateEmployeeDbSchema(BaseModel):
    id:str
    account_id:str
    added_by:str
    shop_id:str
    datas:dict


class UpdateEmployeeDbSchema(BaseModel):
    id:str
    account_id:str
    shop_id:str
    datas:dict