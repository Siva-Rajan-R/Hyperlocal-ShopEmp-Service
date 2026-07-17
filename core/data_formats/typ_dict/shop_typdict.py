from typing import TypedDict,Optional
from ..enums.shop_enums import ShopBusinessTypeEnums,ShopBusinessCurrencyEnums
from datetime import time

try:
    from typing import NotRequired
except ImportError:
    from typing_extensions import NotRequired


class ShopAddressTypDict(TypedDict):
    full_address:str
    zip_code:str
    landmark:str
    latitude:float
    longitude:float

class ShopBusinessGstInfos(TypedDict):
    registered:bool
    number:NotRequired[Optional[str]]


class ShopBusinessInfoTypDict(TypedDict):
    type:ShopBusinessTypeEnums
    gst_infos:ShopBusinessGstInfos
    currency:ShopBusinessCurrencyEnums