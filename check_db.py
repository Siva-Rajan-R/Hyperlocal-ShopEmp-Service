import asyncio
from infras.primary_db.main import AsyncShopEmployeeLocalSession
from sqlalchemy import select
from infras.primary_db.models.employee_model import Employees
from infras.read_db.main import EMPLOYEES_COLLECTION

async def run():
    print("Checking Postgres...")
    async with AsyncShopEmployeeLocalSession() as session:
        res = await session.execute(select(Employees.id).where(Employees.id == 'dd4af079-df87-5ee5-b543-aee736bd7c93'))
        pg_res = res.scalar_one_or_none()
        print('PG:', pg_res)
    
    print("Checking MongoDB...")
    mongo_res = await EMPLOYEES_COLLECTION.find_one({"$or": [{"employee_id": "dd4af079-df87-5ee5-b543-aee736bd7c93"}, {"id": "dd4af079-df87-5ee5-b543-aee736bd7c93"}]})
    print('Mongo:', mongo_res)

asyncio.run(run())
