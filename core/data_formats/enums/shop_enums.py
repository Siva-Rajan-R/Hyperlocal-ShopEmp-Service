from enum import Enum

class ShopTypeEnum(str, Enum):
    RETAIL = "RETAIL"
    WHOLESALE = "WHOLESALE"
    ONLINE = "ONLINE"
    PHYSICAL = "PHYSICAL"