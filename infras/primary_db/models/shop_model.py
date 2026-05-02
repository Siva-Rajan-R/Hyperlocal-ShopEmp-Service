from ..main import BASE
from sqlalchemy import Column, String,ForeignKey,Integer,TIMESTAMP,func,Boolean,Identity,BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB

class Shops(BASE):
    __tablename__="shops"
    id=Column(String,primary_key=True)
    ui_id=Column(BigInteger,Identity(always=True),autoincrement=True)
    sequence_id=Column(BigInteger,Identity(always=True),nullable=False)
    account_id=Column(String,nullable=False)
    name=Column(String,nullable=False)
    category=Column(String,nullable=False)
    business_infos=Column(JSONB,nullable=False)
    address=Column(JSONB,nullable=False)
    image_urls=Column(JSONB,default=list,nullable=True)
    datas=Column(JSONB,nullable=False)
    created_at=Column(TIMESTAMP(timezone=True),nullable=False,server_default=func.now())
    updated_at=Column(TIMESTAMP(timezone=True),nullable=False,server_default=func.now(),onupdate=func.now())
