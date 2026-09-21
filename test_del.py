import asyncio
from infras.primary_db.main import AsyncShopEmployeeLocalSession
from sqlalchemy import delete
from infras.primary_db.models.employee_model import Employees

async def run():
    async with AsyncShopEmployeeLocalSession() as session:
        async with session.begin():
            stmt = delete(Employees).where(Employees.id == 'dd4af079-df87-5ee5-b543-aee736bd7c93')
            res = await session.execute(stmt)
            print('Deleted PG:', res.rowcount)

asyncio.run(run())
