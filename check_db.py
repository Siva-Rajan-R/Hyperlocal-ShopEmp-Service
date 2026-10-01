import asyncio
from sqlalchemy import text
from infras.primary_db.main import AsyncLocalSession

async def main():
    async with AsyncLocalSession() as session:
        res = await session.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'shop_delivery'"))
        for row in res.fetchall():
            print(row[0], ":", row[1])

if __name__ == "__main__":
    asyncio.run(main())
