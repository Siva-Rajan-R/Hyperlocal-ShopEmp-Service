from enum import Enum

class ShopTypeEnum(str, Enum):
    RETAIL = "RETAIL"
    WHOLESALE = "WHOLESALE"
    ONLINE = "ONLINE"
    PHYSICAL = "PHYSICAL"


class ShopBusinessTypeEnums(str,Enum):
    PRIVATE_LIMITED="PRIVATE_LIMITED"
    PARTNERSHIP="PARTNERSHIP"
    SOLO_PROPRIETOR="SOLO_PROPRIETOR"
    LLP="LLP"
    OTHERS="OTHERS"

class ShopBusinessCurrencyEnums(str,Enum):
    INR="INR"
    USD="USD"
    EUR="EUR"