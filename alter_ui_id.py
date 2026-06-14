import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect('postgresql://postgres:TempSuperSecretPwd@89.167.72.254:5432/ShopEmployeeServiceDb')
    await conn.execute('ALTER TABLE employees ALTER COLUMN ui_id DROP IDENTITY IF EXISTS')
    await conn.execute('ALTER TABLE employees ALTER COLUMN ui_id TYPE VARCHAR USING ui_id::VARCHAR')
    print('Altered employees table!')
    await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
