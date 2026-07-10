from pydantic import BaseModel,EmailStr,Field
from core.data_formats.typ_dict.shop_typdict import ShopAddressTypDict
from core.data_formats.enums.employee_enums import EmployeeRoleEnums,EmployeeDepartmentEnums
from core.data_formats.typ_dict.employee_typdict import EmployeeAddressTypDict
from typing import Optional,List,Union
from datetime import date
from hyperlocal_platform.core.enums.timezone_enum import TimeZoneEnum

# Optional Schemas
class EmployeeOptionalFieldsSchema(BaseModel):
    salary_range:Optional[float]=0.0
    address:Optional[EmployeeAddressTypDict]={}

# Writable Schemas
class CreateEmployeeSchema(BaseModel):
    shop_id:str
    name:str
    role:EmployeeRoleEnums
    joined_date:date
    mobile_number:str
    email:EmailStr
    department:EmployeeDepartmentEnums
    additional_infos:Optional[EmployeeOptionalFieldsSchema]={}

class UpdateEmployeeSchema(BaseModel):
    id:str
    shop_id:str
    name:Optional[str]=None
    role:Optional[EmployeeRoleEnums]=None
    joined_date:Optional[date]=None
    mobile_number:Optional[str]=None
    department:Optional[EmployeeDepartmentEnums]=None
    datas:Optional[EmployeeOptionalFieldsSchema]={}


class SendVerifyEmployeeSchema(BaseModel):
    id:str
    shop_id:str

class VerifyEmployeeTokenSchema(BaseModel):
    token:str


class DeleteEmployeeSchema(BaseModel):
    id:str
    shop_id:str


# Fetchable Schemas

class GetAllEmployeesSchema(BaseModel):
    query:Optional[str]=Field(default="",alias="q")
    limit:Optional[int]=Field(default=10,le=100)
    offset:Optional[int]=1
    timezone:Optional[TimeZoneEnum]=TimeZoneEnum.Asia_Kolkata

    model_config={
        "populate_by_name":True
    }

class GetEmployeeByIdSchema(BaseModel):
    shop_id:str
    id:str
    timezone:Optional[TimeZoneEnum]=TimeZoneEnum.Asia_Kolkata

class GetEmployeeByShopIdSchema(BaseModel):
    shop_id:str
    query:Optional[str]=Field(default="",alias="q")
    limit:Optional[int]=Field(default=10,le=100)
    offset:Optional[int]=1
    timezone:Optional[TimeZoneEnum]=TimeZoneEnum.Asia_Kolkata

    model_config={
        "populate_by_name":True
    }

class VerifyEmployeeSchema(BaseModel):
    shop_id:str
    employee_id:Optional[str]=None
    email:Optional[EmailStr]=None
    mobile_number:Optional[str]=None
