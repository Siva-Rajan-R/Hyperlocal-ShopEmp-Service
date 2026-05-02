from typing import TypedDict,Optional
from ..enums.shop_enums import ShopBusinessTypeEnums,ShopBusinessCurrencyEnums
from datetime import time


class EmployeeAddressTypDict(TypedDict):
    full_address:str
    zip_code:str