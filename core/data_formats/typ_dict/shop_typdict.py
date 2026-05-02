from typing import TypedDict,Optional
from ..enums.shop_enums import ShopBusinessTypeEnums,ShopBusinessCurrencyEnums
from datetime import time


class ShopAddressTypDict(TypedDict):
    full_address:str
    zip_code:str
    landmark:str
    latitude:float
    longitude:float

class ShopBusinessInfoTypDict(TypedDict):
    type:ShopBusinessTypeEnums
    gst_no:Optional[str]=None
    opening_time:time
    closing_time:time
    currency:ShopBusinessCurrencyEnums