"""系统配置读写：DB（system_configs 表）中的设置覆盖 .env 默认值。"""
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import SystemConfig

# AI 配置的存储键
KEY_LLM_API_KEY = "llm_api_key"
KEY_LLM_BASE_URL = "llm_base_url"
KEY_LLM_MODEL = "llm_model"


def _db_get(db: Session, key: str) -> str | None:
    row = db.get(SystemConfig, key)
    return row.value if row else None


def get_llm_config(db: Session) -> dict:
    """返回当前生效的 LLM 配置；DB 未设置的项回退到 .env 默认值。"""
    s = get_settings()
    return {
        "api_key": _db_get(db, KEY_LLM_API_KEY) or s.LLM_API_KEY,
        "base_url": _db_get(db, KEY_LLM_BASE_URL) or s.LLM_BASE_URL,
        "model": _db_get(db, KEY_LLM_MODEL) or s.LLM_MODEL,
    }


def set_llm_config(
    db: Session,
    api_key: str | None = None,
    base_url: str | None = None,
    model: str | None = None,
) -> None:
    """更新 LLM 配置。None=保持不变；空串=清除（回退 .env 默认值）。"""
    for key, value in (
        (KEY_LLM_API_KEY, api_key),
        (KEY_LLM_BASE_URL, base_url),
        (KEY_LLM_MODEL, model),
    ):
        if value is None:
            continue
        if value == "":
            row = db.get(SystemConfig, key)
            if row:
                db.delete(row)
        else:
            row = db.get(SystemConfig, key)
            if row:
                row.value = value
            else:
                db.add(SystemConfig(key=key, value=value))
    db.commit()
