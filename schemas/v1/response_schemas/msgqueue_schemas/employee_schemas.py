from pydantic import BaseModel,EmailStr
from core.data_formats.enums.employee_enums import EmployeeDepartmentEnums,EmployeeRoleEnums
from typing import List,Optional
from datetime import datetime,date


class EmployeeCreateResponseSchema(BaseModel):
    id:str
    ui_id:str
    user_id:str
    shop_id:str
    name:str
    email:EmailStr
    mobile_number:str
    role:EmployeeRoleEnums
    department:EmployeeDepartmentEnums
    accepted:bool
    created_at:datetime
    joined_date:date
    datas:Optional[dict]={}

class EmployeeUpdateResponseSchema(BaseModel):
    id:str
    ui_id:str
    user_id:str
    shop_id:str
    name:str
    email:EmailStr
    mobile_number:str
    role:EmployeeRoleEnums
    department:EmployeeDepartmentEnums
    accepted:bool
    created_at:datetime
    updated_at:datetime
    joined_date:date
    datas:Optional[dict]={}

class EmployeeDeleteResponseSchema(BaseModel):
    id:str
    ui_id:str
    user_id:str
    shop_id:str
    name:str
    email:EmailStr
    mobile_number:str
    role:EmployeeRoleEnums
    department:EmployeeDepartmentEnums
    accepted:bool
    created_at:datetime
    updated_at:datetime
    joined_date:date
    datas:Optional[dict]={}



class EmployeeGetResponseSchema(BaseModel):
    id:str
    ui_id:str
    user_id:str
    shop_id:str
    name:str
    email:EmailStr
    mobile_number:str
    role:EmployeeRoleEnums
    department:EmployeeDepartmentEnums
    accepted:bool
    created_at:datetime
    updated_at:datetime
    joined_date:date
    datas:Optional[dict]={}
