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

class DayEnum(str, Enum):
    MONDAY = "MONDAY"
    TUESDAY = "TUESDAY"
    WEDNESDAY = "WEDNESDAY"
    THURSDAY = "THURSDAY"
    FRIDAY = "FRIDAY"
    SATURDAY = "SATURDAY"
    SUNDAY = "SUNDAY"

class DeliveryTypeEnum(str, Enum):
    PICKUP_ONLY = "PICKUP_ONLY"
    INSTANT = "INSTANT"
    STANDARD = "STANDARD"
    NATIONWIDE = "NATIONWIDE"

class DeliveryByEnum(str, Enum):
    INHOUSE = "INHOUSE"
    PARTNERS = "PARTNERS"

class AnnouncementTypeEnum(str, Enum):
    ANNOUNCEMENT = "ANNOUNCEMENT"
    UPDATES = "UPDATES"
    OFFER = "OFFER"

class AnnouncementSendToEnum(str, Enum):
    ALL_FOLLOWED_USERS = "ALL_FOLLOWED_USERS"
    NON_FOLLOWING_USERS = "NON_FOLLOWING_USERS"
    NEW_USER = "NEW_USER"
    PREMIUM = "PREMIUM"

class AnnouncementStatusEnum(str, Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    EXPIRED = "EXPIRED"
    SCHEDULED = "SCHEDULED"
