from pydantic import BaseModel,Field
from core.data_formats.typ_dict.shop_typdict import ShopAddressTypDict,ShopBusinessInfoTypDict
from core.data_formats.enums.shop_enums import ShopTypeEnum
from hyperlocal_platform.core.enums.timezone_enum import TimeZoneEnum
from typing import Optional,Dict,Any

# Optional Fields
class ShopOptionalFieldsSchemas(BaseModel):
    description:Optional[str]=None
    emails:Optional[list]=None
    mobile_numbers:Optional[list]=None
    website:Optional[str]=None



# Writable Schemas
class CreateShopSchema(BaseModel):
    name:str
    category:str
    business_infos:ShopBusinessInfoTypDict
    address:ShopAddressTypDict
    image_urls:Optional[list]=[]
    datas:Optional[ShopOptionalFieldsSchemas]={}


class UpdateShopSchema(BaseModel):
    id:str
    name:Optional[str]=None
    category:Optional[str]=None
    business_infos:Optional[ShopBusinessInfoTypDict]=None
    address:Optional[ShopAddressTypDict]=None
    image_urls:Optional[list]=None
    datas:Optional[ShopOptionalFieldsSchemas]=None


class DeleteShopSchema(BaseModel):
    shop_id:str


# Fetchable Schemas
class GetAllShopsSchema(BaseModel):
    query:Optional[str]=Field(default="",alias="q")
    limit:Optional[int]=Field(default=10,le=100)
    offset:Optional[int]=Field(default=1)
    timezone:Optional[TimeZoneEnum]=Field(default=TimeZoneEnum.Asia_Kolkata)

    model_config={
        "populate_by_name":True
    }


class GetShopByIdSchema(BaseModel):
    shop_id:str
    timezone:Optional[TimeZoneEnum]=Field(default=TimeZoneEnum.Asia_Kolkata)

class GetShopByAccountIdSchema(BaseModel):
    account_id:str
    timezone:Optional[TimeZoneEnum]=Field(default=TimeZoneEnum.Asia_Kolkata)

class VerifyShoSchema(BaseModel):
    shop_id:str