from ..main import BASE
from sqlalchemy import Column, String,ForeignKey,Integer,TIMESTAMP,func,Boolean,Identity,BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB


class Employees(BASE):
    __tablename__="employees"
    id=Column(String,primary_key=True)
    sequence_id=Column(BigInteger,Identity(always=True),nullable=False)
    account_id=Column(String,nullable=False)
    added_by=Column(String,nullable=False)
    shop_id=Column(String,ForeignKey("shops.id",ondelete="CASCADE"),nullable=False)
    datas=Column(JSONB,nullable=False)

    created_at=Column(TIMESTAMP(timezone=True),nullable=False,server_default=func.now())

    shop=relationship("Shops",back_populates="employee")