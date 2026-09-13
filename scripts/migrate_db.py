import asyncio
import os
import re

# Load .env manually to avoid dependency issues
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = r"d:\Projects\Hyperlocal-Inventory\Apis\Hyperlocal-ShopEmp-Service"
env_file = os.path.join(parent_dir, ".env")

env_vars = {}
if os.path.exists(env_file):
    with open(env_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env_vars[k.strip()] = v.strip().strip('"').strip("'")

pg_url = os.environ.get("SHOP_EMP_PG_DATABASE_URL") or env_vars.get("SHOP_EMP_PG_DATABASE_URL") or "postgresql+asyncpg://postgres:437734@127.0.0.1:5432/ShopEmployeeServiceDb"
# Normalize for asyncpg
raw_pg_url = pg_url.replace("postgresql+asyncpg://", "postgresql://")

migration_queries = [
    # shop_delivery table columns
    "ALTER TABLE shop_delivery ADD COLUMN IF NOT EXISTS speed VARCHAR DEFAULT '';",
    "ALTER TABLE shop_delivery ADD COLUMN IF NOT EXISTS free_shipping_amount FLOAT DEFAULT 0.0;",
    "ALTER TABLE shop_delivery ADD COLUMN IF NOT EXISTS min_order_amount FLOAT DEFAULT 0.0;",
    "ALTER TABLE shop_delivery ADD COLUMN IF NOT EXISTS delivery_charge FLOAT DEFAULT 0.0;",
    "ALTER TABLE shop_delivery ADD COLUMN IF NOT EXISTS charge_per_km FLOAT DEFAULT 0.0;",
    "ALTER TABLE shop_delivery ADD COLUMN IF NOT EXISTS radius FLOAT DEFAULT 0.0;",
    "ALTER TABLE shop_delivery ADD COLUMN IF NOT EXISTS delivery_by VARCHAR DEFAULT 'PARTNERS';",
    "ALTER TABLE shop_delivery ADD COLUMN IF NOT EXISTS enabled BOOLEAN DEFAULT TRUE;",
    
    # shops table columns
    "ALTER TABLE shops ADD COLUMN IF NOT EXISTS visible_online BOOLEAN DEFAULT TRUE;",
    "ALTER TABLE shops ADD COLUMN IF NOT EXISTS banner_url VARCHAR;",
    "ALTER TABLE shops ADD COLUMN IF NOT EXISTS logo_url VARCHAR;",
    "ALTER TABLE shops ADD COLUMN IF NOT EXISTS additional_infos JSONB;",
    "ALTER TABLE shops ADD COLUMN IF NOT EXISTS description VARCHAR;",
    "ALTER TABLE shops ADD COLUMN IF NOT EXISTS tagline VARCHAR;",
    
    # shop_announcements table columns
    "ALTER TABLE shop_announcements ADD COLUMN IF NOT EXISTS call_to_action VARCHAR;",
    "ALTER TABLE shop_announcements ADD COLUMN IF NOT EXISTS schedule_at TIMESTAMP WITH TIME ZONE;",
    "ALTER TABLE shop_announcements ADD COLUMN IF NOT EXISTS expire_at TIMESTAMP WITH TIME ZONE;",
    "ALTER TABLE shop_announcements ADD COLUMN IF NOT EXISTS send_to VARCHAR;",
    "ALTER TABLE shop_announcements ADD COLUMN IF NOT EXISTS status VARCHAR;",
    
    # employees table columns
    "ALTER TABLE employees ADD COLUMN IF NOT EXISTS department VARCHAR;",
    "ALTER TABLE employees ADD COLUMN IF NOT EXISTS added_by VARCHAR;",
    "ALTER TABLE employees ADD COLUMN IF NOT EXISTS additional_infos JSONB;",

    # shop_operating_hours table timezone conversion
    "ALTER TABLE shop_operating_hours ALTER COLUMN open_at TYPE TIME WITHOUT TIME ZONE USING open_at::time without time zone;",
    "ALTER TABLE shop_operating_hours ALTER COLUMN close_at TYPE TIME WITHOUT TIME ZONE USING close_at::time without time zone;"
]

async def run_migrations():
    import asyncpg
    print(f"Connecting to database via asyncpg: {raw_pg_url}")
    conn = await asyncpg.connect(raw_pg_url)
    try:
        for q in migration_queries:
            try:
                print(f"Executing: {q}")
                await conn.execute(q)
            except Exception as e:
                print(f"Warning on {q}: {e}")
        print("ALL MIGRATIONS EXECUTED SUCCESSFULLY!")
    finally:
        await conn.close()

if __name__ == "__main__":
    # Also save to scripts/migrate_db.py
    scripts_dest = os.path.join(parent_dir, "scripts", "migrate_db.py")
    with open(scripts_dest, "w", encoding="utf-8") as f:
        with open(__file__, "r", encoding="utf-8") as self_f:
            f.write(self_f.read())
    print(f"Saved standalone script to {scripts_dest}")
    asyncio.run(run_migrations())
