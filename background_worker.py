import os
import asyncio
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import update, or_, and_
from core.configs.settings_config import SETTINGS
from infras.primary_db.models.shop_model import ShopAnnouncements
from core.data_formats.enums.shop_enums import AnnouncementStatusEnum
from arq import cron
from arq.connections import RedisSettings

redis_url = os.getenv("PLATFORM_REDIS_URL", "redis://localhost:6379")
redis_settings = RedisSettings.from_dsn(redis_url)

# Create database engine
engine = create_async_engine(SETTINGS.PG_DATABASE_URL)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

async def check_and_update_announcements(ctx):
    """
    Cron task that runs periodically to:
    1. Update scheduled announcements to 'published' if schedule_at <= current_time.
    2. Update published/scheduled announcements to 'expired' if expire_at <= current_time.
    """
    now = datetime.now(timezone.utc)
    async with SessionLocal() as session:
        async with session.begin():
            # 1. Update scheduled -> published
            stmt1 = (
                update(ShopAnnouncements)
                .where(
                    and_(
                        ShopAnnouncements.status == AnnouncementStatusEnum.SCHEDULED.value,
                        ShopAnnouncements.schedule_at <= now
                    )
                )
                .values(status=AnnouncementStatusEnum.PUBLISHED.value)
            )
            await session.execute(stmt1)

            # 2. Update published/scheduled -> expired
            stmt2 = (
                update(ShopAnnouncements)
                .where(
                    and_(
                        ShopAnnouncements.status.in_([
                            AnnouncementStatusEnum.PUBLISHED.value,
                            AnnouncementStatusEnum.SCHEDULED.value
                        ]),
                        ShopAnnouncements.expire_at.is_not(None),
                        ShopAnnouncements.expire_at <= now
                    )
                )
                .values(status=AnnouncementStatusEnum.EXPIRED.value)
            )
            await session.execute(stmt2)

async def startup(ctx):
    pass

async def shutdown(ctx):
    await engine.dispose()

class WorkerSettings:
    redis_settings = redis_settings
    on_startup = startup
    on_shutdown = shutdown
    cron_jobs = [
        cron(check_and_update_announcements, second={0, 10, 20, 30, 40, 50})
    ]
