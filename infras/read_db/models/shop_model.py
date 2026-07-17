from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class ReadDbShopCreateModel(BaseModel):
    id: str
    ui_id: Optional[int] = None
    sequence_id: Optional[int] = None
    user_id: str
    name: str
    description: Optional[str] = None
    tagline: Optional[str] = None
    categories: List[str] = []
    business_infos: Dict[str, Any] = {}
    address: Dict[str, Any] = {}
    banner_url: Optional[str] = None
    logo_url: Optional[str] = None
    additional_infos: Optional[Dict[str, Any]] = {}  # mapped from additional_infos
    visible_online: bool = False
    operating_hours: List[Dict[str, Any]] = []
    delivery_options: List[Dict[str, Any]] = []
    announcements: List[Dict[str, Any]] = []

class ReadDbShopUpdateModel(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    tagline: Optional[str] = None
    categories: Optional[List[str]] = None
    business_infos: Optional[Dict[str, Any]] = None
    address: Optional[Dict[str, Any]] = None
    banner_url: Optional[str] = None
    logo_url: Optional[str] = None
    additional_infos: Optional[Dict[str, Any]] = None
    visible_online: Optional[bool] = None
    operating_hours: Optional[List[Dict[str, Any]]] = None
    delivery_options: Optional[List[Dict[str, Any]]] = None
    announcements: Optional[List[Dict[str, Any]]] = None

class ReadDbShopReadModel(ReadDbShopCreateModel):
    ...
