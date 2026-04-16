from pydantic import ValidationError
from pydantic_settings import BaseSettings
from typing import Callable
from ..settings import ShopEmployeeSettings
import sys
from ..constants import ENV_PREFIX,FULL_SERVICE_NAME
from hyperlocal_platform.core.utils.settings_initializer import init_settings


SETTINGS: ShopEmployeeSettings = init_settings(settings=ShopEmployeeSettings,service_name=FULL_SERVICE_NAME,env_prefix=ENV_PREFIX)
