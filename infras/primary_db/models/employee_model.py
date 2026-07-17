from ..main import BASE
from sqlalchemy import Column, String,ForeignKey,Integer,TIMESTAMP,func,Boolean,Identity,BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB


class Employees(BASE):
    __tablename__="employees"
    id=Column(String,primary_key=True)
    shop_id=Column(String,nullable=False)
    ui_id=Column(String,nullable=False,index=True)
    sequence_id=Column(BigInteger,Identity(always=True),nullable=False)
    user_id=Column(String,nullable=False,index=True)
    name=Column(String,nullable=False)
    role=Column(String,nullable=False)
    joined_date=Column(TIMESTAMP,nullable=False)
    department=Column(String,nullable=False)
    accepted=Column(Boolean,nullable=False)
    added_by=Column(String,nullable=False)
    additional_infos=Column(JSONB,nullable=False)
    

    created_at=Column(TIMESTAMP(timezone=True),nullable=False,server_default=func.now())
    updated_at=Column(TIMESTAMP(timezone=True),nullable=False,server_default=func.now(),onupdate=func.now())