from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Kunpeng Yidao API"
    debug: bool = True

    # JWT
    secret_key: str = "change-this-secret-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 8

    # Database
    mysql_user: str = "kunpeng"
    mysql_password: str = "HdPBDCX"
    mysql_host: str = "127.0.0.1"
    mysql_port: int = 3306
    mysql_db: str = "kunpeng"

    # DeepSeek API（优先从环境变量 DEEPSEEK_API_KEY 读取，生产环境请务必使用环境变量）
    deepseek_api_key: str = "sk-14fbbf6af88a4f31b143d16d3441e2f2"

    class Config:
        env_prefix = "KUNPENG_"
        extra = "ignore"

    def get_deepseek_api_key(self) -> str:
        """优先使用环境变量 DEEPSEEK_API_KEY（无 KUNPENG_ 前缀）"""
        import os
        return os.environ.get("DEEPSEEK_API_KEY") or self.deepseek_api_key or ""


@lru_cache()
def get_settings() -> Settings:
    return Settings()

