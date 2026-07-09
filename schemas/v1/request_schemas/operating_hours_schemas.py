from pydantic import BaseModel, Field
from datetime import datetime,time
from core.data_formats.enums.shop_enums import DayEnum
from typing import Optional

class CreateOperatingHoursSchema(BaseModel):
    open_at: time
    close_at: time
    day: DayEnum

class UpdateOperatingHoursSchema(BaseModel):
    id: int
    open_at: Optional[time] = None
    close_at: Optional[time] = None
    day: Optional[DayEnum] = None
