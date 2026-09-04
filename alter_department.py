import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect('postgresql://postgres:437734@127.0.0.1:5432/ShopEmployeeServiceDb')
    await conn.execute('ALTER TABLE employees ALTER COLUMN department DROP NOT NULL')
    print('Altered employees table department column!')
    await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
