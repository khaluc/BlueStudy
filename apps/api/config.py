from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, SecretStr


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')
    database_url: str = 'sqlite:///data/development.db'
    storage_root: Path = Path('data/uploads')
    local_access_file: Path | None = None
    chat_base_url: str = 'http://127.0.0.1:8001'
    worker_poll_seconds: float = Field(default=2, ge=0.1, le=60)
    assemblyai_api_key: SecretStr = SecretStr('')
    assemblyai_speech_model: str = 'universal-3-5-pro'
