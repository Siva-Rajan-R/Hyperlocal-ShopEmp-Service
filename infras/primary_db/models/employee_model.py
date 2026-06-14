from ..main import BASE
from sqlalchemy import Column, String,ForeignKey,Integer,TIMESTAMP,func,Boolean,Identity,BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB


class Employees(BASE):
    __tablename__="employees"
    id=Column(String,primary_key=True)
    ui_id=Column(String,nullable=False,index=True)
    sequence_id=Column(BigInteger,Identity(always=True),nullable=False)
    account_id=Column(String,nullable=False)
    name=Column(String,nullable=False)
    role=Column(String,nullable=False)
    mobile_number=Column(String,nullable=False)
    email=Column(String,nullable=False)
    joined_date=Column(TIMESTAMP,nullable=False)
    department=Column(String,nullable=False)
    added_by=Column(String,nullable=False)
    datas=Column(JSONB,nullable=False)
    shop_id=Column(String,nullable=False)

    created_at=Column(TIMESTAMP(timezone=True),nullable=False,server_default=func.now())
    updated_at=Column(TIMESTAMP(timezone=True),nullable=False,server_default=func.now(),onupdate=func.now())