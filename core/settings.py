from pydantic_settings import BaseSettings
from pydantic import Field
from hyperlocal_platform.core.enums.environment_enum import EnvironmentEnum
from .constants import ENV_PREFIX
from dotenv import load_dotenv
load_dotenv()

class ShopEmployeeSettings(BaseSettings):
    PG_DATABASE_URL:str
    MONGO_DB_URL:str
    ENVIRONMENT:EnvironmentEnum
    DEB_SECRETS:str
    DEB_APIKEY:str
    BACKEND_BASE_URL:str
    FRONTEND_BASE_URL:str
    SMTP_HOST:str
    SMTP_PORT:int
    SMTP_USER:str
    SMTP_PASS:str

    model_config={
        "case_sensitive":False,
        "env_prefix":ENV_PREFIX
    }