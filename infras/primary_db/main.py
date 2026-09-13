from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import text
from core.configs.settings_config import SETTINGS
from icecream import ic


ENGINE=create_async_engine(SETTINGS.PG_DATABASE_URL,echo=False, pool_size=5, max_overflow=10, pool_recycle=1800, pool_pre_ping=True)

BASE=declarative_base()


AsyncShopEmployeeLocalSession=async_sessionmaker(ENGINE)

async def init_shop_employee_pg_db():
    try:
        ic("initializing pg db...")
        async with ENGINE.connect() as conn:
            # await conn.run_sync(BASE.metadata.drop_all)
            await conn.run_sync(BASE.metadata.create_all)
            
            # Auto-migration for schema upgrades across environments
            migration_queries = [
                # shop_delivery columns
                "ALTER TABLE shop_delivery ADD COLUMN IF NOT EXISTS speed VARCHAR DEFAULT '';",
                "ALTER TABLE shop_delivery ADD COLUMN IF NOT EXISTS free_shipping_amount FLOAT DEFAULT 0.0;",
                "ALTER TABLE shop_delivery ADD COLUMN IF NOT EXISTS min_order_amount FLOAT DEFAULT 0.0;",
                "ALTER TABLE shop_delivery ADD COLUMN IF NOT EXISTS delivery_charge FLOAT DEFAULT 0.0;",
                "ALTER TABLE shop_delivery ADD COLUMN IF NOT EXISTS charge_per_km FLOAT DEFAULT 0.0;",
                "ALTER TABLE shop_delivery ADD COLUMN IF NOT EXISTS radius FLOAT DEFAULT 0.0;",
                "ALTER TABLE shop_delivery ADD COLUMN IF NOT EXISTS delivery_by VARCHAR DEFAULT 'PARTNERS';",
                "ALTER TABLE shop_delivery ADD COLUMN IF NOT EXISTS enabled BOOLEAN DEFAULT TRUE;",
                
                # shops columns
                "ALTER TABLE shops ADD COLUMN IF NOT EXISTS visible_online BOOLEAN DEFAULT TRUE;",
                "ALTER TABLE shops ADD COLUMN IF NOT EXISTS banner_url VARCHAR;",
                "ALTER TABLE shops ADD COLUMN IF NOT EXISTS logo_url VARCHAR;",
                "ALTER TABLE shops ADD COLUMN IF NOT EXISTS additional_infos JSONB;",
                "ALTER TABLE shops ADD COLUMN IF NOT EXISTS description VARCHAR;",
                "ALTER TABLE shops ADD COLUMN IF NOT EXISTS tagline VARCHAR;",
                
                # shop_announcements columns
                "ALTER TABLE shop_announcements ADD COLUMN IF NOT EXISTS call_to_action VARCHAR;",
                "ALTER TABLE shop_announcements ADD COLUMN IF NOT EXISTS schedule_at TIMESTAMP WITH TIME ZONE;",
                "ALTER TABLE shop_announcements ADD COLUMN IF NOT EXISTS expire_at TIMESTAMP WITH TIME ZONE;",
                "ALTER TABLE shop_announcements ADD COLUMN IF NOT EXISTS send_to VARCHAR;",
                "ALTER TABLE shop_announcements ADD COLUMN IF NOT EXISTS status VARCHAR;",
                
                # employees columns
                "ALTER TABLE employees ADD COLUMN IF NOT EXISTS department VARCHAR;",
                "ALTER TABLE employees ADD COLUMN IF NOT EXISTS added_by VARCHAR;",
                "ALTER TABLE employees ADD COLUMN IF NOT EXISTS additional_infos JSONB;"
            ]
            for query in migration_queries:
                try:
                    await conn.execute(text(query))
                except Exception as mig_err:
                    ic(f"Migration statement skipped: {query} => {mig_err}")
            await conn.commit()
            
        ic("...Database initialized and migrated successfully...")
    except Exception as e:
        ic(f"Error : initializing pg db => {e}")


async def get_pg_async_session():
    Session=AsyncShopEmployeeLocalSession()
    try:
        yield Session
    finally:
        await Session.close()
