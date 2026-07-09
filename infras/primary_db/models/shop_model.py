from ..main import BASE
from sqlalchemy import Column, String,ForeignKey,Integer,TIMESTAMP,func,Boolean,Identity,BigInteger,ARRAY,Float,Time
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB

class Shops(BASE):
    __tablename__="shops"
    id=Column(String,primary_key=True)
    ui_id=Column(BigInteger,Identity(always=True),autoincrement=True)
    sequence_id=Column(BigInteger,Identity(always=True),nullable=False)
    user_id=Column(String,nullable=False)
    name=Column(String,nullable=False)
    description=Column(String,nullable=True)
    tagline=Column(String,nullable=True)
    categories=Column(ARRAY(String),nullable=False)
    business_infos=Column(JSONB,nullable=False)
    address=Column(JSONB,nullable=False)
    banner_url=Column(String,nullable=True)
    logo_url=Column(String,nullable=True)
    additional_infos=Column(JSONB,nullable=True)
    visible_online=Column(Boolean,nullable=False)
    created_at=Column(TIMESTAMP(timezone=True),nullable=False,server_default=func.now())
    updated_at=Column(TIMESTAMP(timezone=True),nullable=False,server_default=func.now(),onupdate=func.now())

    operating_hours = relationship("ShopOperatingHours", back_populates="shop", cascade="all, delete-orphan", lazy="selectin")
    delivery_options = relationship("ShopDelivery", back_populates="shop", cascade="all, delete-orphan", lazy="selectin")
    announcements = relationship("ShopAnnouncements", back_populates="shop", cascade="all, delete-orphan", lazy="selectin")


class ShopFollowers(BASE):
    __tablename__="shop_followers"
    id=Column(BigInteger,primary_key=True,autoincrement=True)
    shop_id=Column(String,ForeignKey("shops.id", ondelete="CASCADE"),nullable=False)
    user_id=Column(String,nullable=False)

    created_at=Column(TIMESTAMP(timezone=True),nullable=False,server_default=func.now())
    updated_at=Column(TIMESTAMP(timezone=True),nullable=False,server_default=func.now(),onupdate=func.now())


class ShopOperatingHours(BASE):
    __tablename__="shop_operating_hours"
    id=Column(BigInteger,primary_key=True,autoincrement=True)
    shop_id=Column(String,ForeignKey("shops.id", ondelete="CASCADE"),nullable=False)
    open_at=Column(Time(timezone=True),nullable=False)
    close_at=Column(Time(timezone=True),nullable=False)
    day=Column(String,nullable=False)

    shop = relationship("Shops", back_populates="operating_hours")


class ShopDelivery(BASE):
    __tablename__="shop_delivery"
    id=Column(BigInteger,primary_key=True,autoincrement=True)
    shop_id=Column(String,ForeignKey("shops.id", ondelete="CASCADE"),nullable=False)
    type=Column(String,nullable=False)
    speed=Column(String,nullable=False)
    free_shipping_amount=Column(Float,nullable=False)
    delivery_by=Column(String,nullable=False)

    shop = relationship("Shops", back_populates="delivery_options")


class ShopAnnouncements(BASE):
    __tablename__="shop_announcements"
    id=Column(BigInteger,primary_key=True,autoincrement=True)
    shop_id=Column(String,ForeignKey("shops.id", ondelete="CASCADE"),nullable=False)
    type=Column(String,nullable=False)
    message=Column(String,nullable=False) 
    call_to_action=Column(String,nullable=True)
    schedule_at=Column(TIMESTAMP(timezone=True),nullable=True)
    expire_at=Column(TIMESTAMP(timezone=True),nullable=True)
    send_to=Column(String,nullable=False)
    status=Column(String,nullable=False)

    created_at=Column(TIMESTAMP(timezone=True),nullable=False,server_default=func.now())
    updated_at=Column(TIMESTAMP(timezone=True),nullable=False,server_default=func.now(),onupdate=func.now())

    shop = relationship("Shops", back_populates="announcements")



