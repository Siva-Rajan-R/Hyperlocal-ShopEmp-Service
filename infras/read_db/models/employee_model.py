from pydantic import BaseModel,EmailStr
from core.data_formats.enums.role_enums import RoleEnum
from typing import Optional

class ReadDbEmployeeCreateModel(BaseModel):
    employee_id:str
    account_id:str
    shop_id:str
    name:str
    email:EmailStr
    mobile_number:str
    is_accepted:bool
    added_by:str
    role:str

class ReadDbEmployeeUpdateModel(BaseModel):
    name:Optional[str]=None
    is_accepted:Optional[bool]=None
    role:Optional[str]=None
    mobile_number:Optional[str]=None

class ReadDbEmployeeReadModel(ReadDbEmployeeCreateModel):
    ...