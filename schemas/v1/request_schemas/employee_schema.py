from pydantic import BaseModel,EmailStr
from core.data_formats.typ_dict.shop_typdict import ShopAddressTypDict
from core.data_formats.enums.role_enums import RoleEnum
from typing import Optional

class CreateEmployeeSchema(BaseModel):
    shop_id:str
    datas:dict

class UpdateEmployeeSchema(BaseModel):
    id:str
    account_id:str
    shop_id:str
    datas:dict
