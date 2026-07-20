from pydantic import BaseModel,Field
from core.data_formats.typ_dict.shop_typdict import ShopAddressTypDict,ShopBusinessInfoTypDict
from core.data_formats.enums.shop_enums import ShopTypeEnum
from hyperlocal_platform.core.enums.timezone_enum import TimeZoneEnum
from typing import Optional,Dict,Any,List
from schemas.v1.request_schemas.operating_hours_schemas import CreateOperatingHoursSchema
from schemas.v1.request_schemas.delivery_schemas import CreateDeliverySchema

# Optional Fields
class ShopOptionalFieldsSchemas(BaseModel):
    emails:Optional[list]=None
    mobile_numbers:Optional[list]=None
    website:Optional[str]=None



# Writable Schemas
class CreateShopSchema(BaseModel):
    name:str
    description:Optional[str]=None
    tagline:Optional[str]=None
    categories:List[str]
    business_infos:ShopBusinessInfoTypDict
    address:ShopAddressTypDict
    additional_infos:Optional[ShopOptionalFieldsSchemas]={}
    visible_online:Optional[bool]=False
    operating_hours:Optional[List[CreateOperatingHoursSchema]]=None
    delivery_options:Optional[List[CreateDeliverySchema]]=None


class UpdateShopSchema(BaseModel):
    id:str
    name:Optional[str]=None
    categories:Optional[List[str]]=None
    business_infos:Optional[ShopBusinessInfoTypDict]=None
    address:Optional[ShopAddressTypDict]=None
    logo_url:Optional[str]=None
    banner_url:Optional[str]=None
    additional_infos:Optional[ShopOptionalFieldsSchemas]=None
    visible_online:Optional[bool]=None
    operating_hours:Optional[List[CreateOperatingHoursSchema]]=None
    delivery_options:Optional[List[CreateDeliverySchema]]=None




class DeleteShopSchema(BaseModel):
    shop_id:str


# Fetchable Schemas
class GetAllShopsSchema(BaseModel):
    query:Optional[str]=Field(default="",alias="q")
    limit:Optional[int]=Field(default=10,le=100)
    offset:Optional[int]=Field(default=1)
    timezone:Optional[TimeZoneEnum]=Field(default=TimeZoneEnum.Asia_Kolkata)
    visible_online:Optional[bool]=None

    model_config={
        "populate_by_name":True
    }


class GetShopByIdSchema(BaseModel):
    shop_id:str
    timezone:Optional[TimeZoneEnum]=Field(default=TimeZoneEnum.Asia_Kolkata)

class GetShopByUserIdSchema(BaseModel):
    user_id:str
    timezone:Optional[TimeZoneEnum]=Field(default=TimeZoneEnum.Asia_Kolkata)

class VerifyShoSchema(BaseModel):
    shop_id:str

class ShopFollowerSchema(BaseModel):
    shop_id: str
    user_id: str

class GetBulkShopsByIdSchema(BaseModel):
    shop_ids: List[str]
    timezone: Optional[TimeZoneEnum] = Field(default=TimeZoneEnum.Asia_Kolkata)