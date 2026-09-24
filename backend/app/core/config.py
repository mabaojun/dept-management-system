from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "部门数字化管理终端"
    SECRET_KEY: str = "dev-secret-change-me-in-production"
    ALGORITHM: str = "HS256"
    TOKEN_EXPIRE_DAYS: int = 7

    # 本地快速启动默认 SQLite；docker-compose / 线上使用 PostgreSQL
    DATABASE_URL: str = "sqlite:///./dev.db"

    CORS_ORIGINS: str = "http://localhost:5174"

    # LLM 配置（OpenAI 兼容协议：DeepSeek / Qwen / GLM 均可）
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "https://api.deepseek.com/v1"
    LLM_MODEL: str = "deepseek-chat"

    # 初始管理员
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin123"
    ADMIN_NAME: str = "系统管理员"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
