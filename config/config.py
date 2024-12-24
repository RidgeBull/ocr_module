from typing import Any, Callable, Set
from pydantic import (
    AliasChoices,
    AmqpDsn,
    BaseModel,
    Field,
    ImportString,
    PostgresDsn,
    RedisDsn,
)
from pydantic_settings import BaseSettings, SettingsConfigDict
import os

def _get_env_file() -> str:
    ret = os.path.join(os.path.dirname(__file__), "../.env")
    print("-----------------")
    with open(ret) as f:
        print(f.read())
    print("-----------------")
    return ret

# Define the settings model
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_get_env_file(),
    )
    AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT: str
    AZURE_DOCUMENT_INTELLIGENCE_KEY: str


# Load the settings
settings = Settings()