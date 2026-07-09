from pydantic import BaseModel, Field
from datetime import datetime
from core.data_formats.enums.shop_enums import AnnouncementTypeEnum, AnnouncementSendToEnum, AnnouncementStatusEnum
from typing import Optional

class CreateAnnouncementSchema(BaseModel):
    type: AnnouncementTypeEnum
    message: str
    call_to_action: Optional[str] = None
    schedule_at: Optional[datetime] = None
    expire_at: Optional[datetime] = None
    send_to: AnnouncementSendToEnum
    status: AnnouncementStatusEnum

class UpdateAnnouncementSchema(BaseModel):
    id: int
    type: Optional[AnnouncementTypeEnum] = None
    message: Optional[str] = None
    call_to_action: Optional[str] = None
    schedule_at: Optional[datetime] = None
    expire_at: Optional[datetime] = None
    send_to: Optional[AnnouncementSendToEnum] = None
    status: Optional[AnnouncementStatusEnum] = None
