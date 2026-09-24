"""系统配置 API（仅管理员）：AI 接口的查看 / 修改 / 连通性测试。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.db.base import get_db
from app.models import User
from app.schemas import AiConfigIn, AiConfigOut
from app.services import ai
from app.services.sysconfig import get_llm_config, set_llm_config

router = APIRouter(prefix="/config", tags=["config"])


def _build_out(db: Session) -> AiConfigOut:
    cfg = get_llm_config(db)
    api_key = cfg["api_key"]
    return AiConfigOut(
        base_url=cfg["base_url"],
        model=cfg["model"],
        api_key_set=bool(api_key),
        api_key_tail=api_key[-4:] if api_key else "",
        mock_mode=not api_key,
    )


@router.get("/ai", response_model=AiConfigOut)
def get_ai_config(
    _: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    return _build_out(db)


@router.put("/ai", response_model=AiConfigOut)
def update_ai_config(
    body: AiConfigIn,
    _: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    if body.base_url is not None and body.base_url and not body.base_url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="Base URL 必须以 http:// 或 https:// 开头")
    if body.model is not None and body.model == "":
        raise HTTPException(status_code=400, detail="模型名称不能为空")
    set_llm_config(db, api_key=body.api_key, base_url=body.base_url, model=body.model)
    return _build_out(db)


@router.post("/ai/test")
def test_ai_config(
    _: User = Depends(require_roles("admin")),
):
    """发送一条极小请求验证 AI 接口连通性。"""
    if ai.is_mock_mode():
        raise HTTPException(status_code=400, detail="尚未配置 API Key，无法测试")
    try:
        reply = ai.test_connection()
    except Exception as e:  # 网络/鉴权/模型名错误等
        raise HTTPException(status_code=400, detail=f"连接失败：{e}") from e
    return {"ok": True, "reply": reply}
