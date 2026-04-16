from fastapi import FastAPI
from api.routers.v1 import employee_routes,shop_routes
from infras.primary_db.main import init_shop_employee_pg_db
from contextlib import asynccontextmanager
from icecream import ic
from dotenv import load_dotenv
from core.configs.settings_config import SETTINGS
from hyperlocal_platform.core.enums.environment_enum import EnvironmentEnum
import os,asyncio
from hyperlocal_platform.infras.saga.main import init_infra_db
from messaging.worker import worker
from infras.read_db.main import EMPLOYEES_COLLECTION
load_dotenv()


@asynccontextmanager
async def shop_employee_service_lifespan(app:FastAPI):
    try:
        ic("Starting Shop-Employee service...")
        await init_shop_employee_pg_db()
        await init_infra_db()
        asyncio.create_task(worker())
        yield

    except Exception as e:
        ic(f"Error : Starting Shop-Employee service => {e}")

    finally:
        ic("...Stoping Shop-Employee Servcie...")

debug=False
openapi_url=None
docs_url=None
redoc_url=None

if SETTINGS.ENVIRONMENT.value==EnvironmentEnum.DEVELOPMENT.value:
    debug=True
    openapi_url="/openapi.json"
    docs_url="/docs"
    redoc_url="/redoc"

app=FastAPI(
    title="Shop-Employee Service",
    description="This service contains all the CRUD operations for Shop-Employee service",
    debug=debug,
    openapi_url=openapi_url,
    docs_url=docs_url,
    redoc_url=redoc_url,
    lifespan=shop_employee_service_lifespan
)



# Routes to include
app.include_router(shop_routes.router)
app.include_router(employee_routes.router)


