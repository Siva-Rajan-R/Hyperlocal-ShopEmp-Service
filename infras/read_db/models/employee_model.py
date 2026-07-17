from pydantic import BaseModel,EmailStr
from core.data_formats.enums.employee_enums import EmployeeRoleEnums
from typing import Optional

class ReadDbEmployeeCreateModel(BaseModel):
    employee_id:str
    user_id:str
    shop_id:str
    name:str
    email:EmailStr
    mobile_number:str
    is_accepted:bool
    added_by:str
    role:str
    joined_date:Optional[str]=None
    department:Optional[str]=None
    additional_infos:Optional[dict]=None

class ReadDbEmployeeUpdateModel(BaseModel):
    name:Optional[str]=None
    is_accepted:Optional[bool]=None
    role:Optional[str]=None
    mobile_number:Optional[str]=None
    email:Optional[EmailStr]=None
    joined_date:Optional[str]=None
    department:Optional[str]=None
    additional_infos:Optional[dict]=None

class ReadDbEmployeeReadModel(ReadDbEmployeeCreateModel):
    ...