from ..main import BASE
from sqlalchemy import Column, String,ForeignKey,Integer,TIMESTAMP,func,Boolean,Identity,BigInteger,ARRAY
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
    created_at=Column(TIMESTAMP(timezone=True),nullable=False,server_default=func.now())
    updated_at=Column(TIMESTAMP(timezone=True),nullable=False,server_default=func.now(),onupdate=func.now())
