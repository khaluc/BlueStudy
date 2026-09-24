from typing import Literal
from urllib.parse import urlsplit
from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class CloudSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')
    chat_provider: Literal['ollama', 'qwen_cloud'] = 'ollama'
    vision_provider: Literal['tesseract', 'ollama'] = 'ollama'
    ollama_base_url: str = 'http://127.0.0.1:11434'
    ollama_vision_model: str = 'qwen3-vl:2b-instruct-q8_0'
    vision_timeout_seconds: float = Field(default=45, gt=0, le=90)
    dashscope_api_key: SecretStr = SecretStr('')
    qwen_base_url: str = 'https://maas.qwencloudapi.com/compatible-mode/v1'
    qwen_chat_model: str = 'qwen3.8-max-0902'
    qwen_enable_thinking: bool = True
    qwen_max_tokens: int = Field(default=4096, ge=256, le=16384)
    cloud_timeout_seconds: float = Field(default=45, gt=0, le=90)
    local_fallback_enabled: bool = True

    @field_validator('qwen_base_url')
    @classmethod
    def https_endpoint(cls, value):
        parsed = urlsplit(value)
        if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError('Qwen endpoint must use HTTPS without embedded credentials/query.')
        return value.rstrip('/')
