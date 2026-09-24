from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from packages.llm.cloud_config import CloudSettings


class Settings(CloudSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')
    ollama_base_url: str = 'http://127.0.0.1:11434'
    ollama_model: str = 'gemma4:e2b'
    llm_timeout_seconds: float = Field(default=120, gt=0, le=600)
    llm_num_ctx: int = Field(default=4096, ge=1024, le=32768)
    llm_num_predict: int = Field(default=512, ge=64, le=4096)
