from pydantic import BaseModel,EmailStr
from core.data_formats.typ_dict.employee_typdict import EmployeeAddressTypDict
from core.data_formats.enums.employee_enums import EmployeeDepartmentEnums,EmployeeRoleEnums
from typing import Optional,List,Union
from datetime import date
from ..request_schemas.employee_schemas import EmployeeOptionalFieldsSchema

class CreateEmployeeDbSchema(BaseModel):
    id:str
    ui_id:str
    user_id:str
    added_by:str
    shop_id:str
    role:EmployeeRoleEnums
    joined_date:date
    department:EmployeeDepartmentEnums
    accepted:bool
    additional_infos:Optional[EmployeeOptionalFieldsSchema]={}


class UpdateEmployeeDbSchema(BaseModel):
    id:str
    shop_id:str
    role:Optional[EmployeeRoleEnums]=None
    joined_date:Optional[date]=None
    department:Optional[EmployeeDepartmentEnums]=None
    accepted:Optional[bool]=None
    additional_infos:Optional[dict]={}