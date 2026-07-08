from ..main import BASE
from sqlalchemy import Column, String,ForeignKey,Integer,TIMESTAMP,func,Boolean,Identity,BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB


class Users(BASE):
    __tablename__="users"
    id=Column(String,primary_key=True)
    sequence_id=Column(BigInteger,Identity(always=True),nullable=False)
    name=Column(String,nullable=False)
    mobile_number=Column(String,nullable=True)
    email=Column(String,nullable=False,unique=True)
    additional_infos=Column(JSONB,nullable=False)
    

    created_at=Column(TIMESTAMP(timezone=True),nullable=False,server_default=func.now())
    updated_at=Column(TIMESTAMP(timezone=True),nullable=False,server_default=func.now(),onupdate=func.now())