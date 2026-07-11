from pydantic import BaseModel
from core.data_formats.typ_dict.shop_typdict import ShopAddressTypDict,ShopBusinessInfoTypDict
from core.data_formats.enums.shop_enums import ShopTypeEnum
from typing import Optional,List
from ..request_schemas.shop_schemas import ShopOptionalFieldsSchemas


class CreateShopDbSchema(BaseModel):
    id:str
    user_id:str
    name:str
    description:Optional[str]=None
    tagline:Optional[str]=None
    categories:List[str]
    business_infos:ShopBusinessInfoTypDict
    address:ShopAddressTypDict
    logo_url:Optional[str]=None
    banner_url:Optional[str]=None
    additional_infos:Optional[ShopOptionalFieldsSchemas]={}
    visible_online:bool = False


class UpdateShopDbSchema(BaseModel):
    id:str
    user_id:str
    name:Optional[str]=None
    category:Optional[str]=None
    address:Optional[ShopAddressTypDict]=None
    business_infos:Optional[ShopBusinessInfoTypDict]=None
    image_urls:Optional[list]=[]
    logo_url:Optional[str]=None
    banner_url:Optional[str]=None
    datas:Optional[dict]={}
    visible_online:Optional[bool]=None


class DeleteShopDbSchema(BaseModel):
    shop_id:str
    user_id:str