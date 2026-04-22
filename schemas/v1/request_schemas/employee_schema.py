from pydantic import BaseModel,EmailStr
from core.data_formats.typ_dict.shop_typdict import ShopAddressTypDict
from core.data_formats.enums.role_enums import RoleEnum
from typing import Optional

CREATE_EMPLOYEE_MANDATORY_FIELDS={
    "email":str,
    "name":str,
    "mobile_number":str,
    'role':str,
    "shop_id":str,
}

class CreateEmployeeSchema(BaseModel):
    datas:dict


UPDATE_EMPLOYEE_MANDATORY_FIELDS={
    "id":str,
    "account_id":str,
    "shop_id":str,
    
    "email":str,
    "name":str,
    "mobile_number":str,
    'role':str,
}

class UpdateEmployeeSchema(BaseModel):
    datas:dict
