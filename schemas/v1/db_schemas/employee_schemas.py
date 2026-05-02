from pydantic import BaseModel,EmailStr
from core.data_formats.typ_dict.employee_typdict import EmployeeAddressTypDict
from core.data_formats.enums.employee_enums import EmployeeDepartmentEnums,EmployeeRoleEnums
from typing import Optional,List,Union
from datetime import date

class CreateEmployeeDbSchema(BaseModel):
    id:str
    account_id:str
    added_by:str
    shop_id:str
    name:str
    role:EmployeeRoleEnums
    joined_date:date
    mobile_number:str
    email:EmailStr
    department:EmployeeDepartmentEnums
    datas:Optional[dict]={}


class UpdateEmployeeDbSchema(BaseModel):
    id:str
    shop_id:str
    name:Optional[str]=None
    role:Optional[EmployeeRoleEnums]=None
    joined_date:Optional[date]=None
    mobile_number:Optional[str]=None
    department:Optional[EmployeeDepartmentEnums]=None
    datas:Optional[dict]={}