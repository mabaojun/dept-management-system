from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_roles
from app.db.base import get_db
from app.models import PeriodReport, User
from app.schemas import PeriodReportOut, ReportGenerateIn
from app.services.report import generate_period_report

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("", response_model=list[PeriodReportOut])
def list_reports(
    limit: int = 50,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """阶段工作总结列表（全员可见，新的在前）。"""
    return (
        db.query(PeriodReport)
        .order_by(PeriodReport.period_end.desc(), PeriodReport.id.desc())
        .limit(min(limit, 100))
        .all()
    )


@router.post("/generate", response_model=PeriodReportOut, status_code=201)
def generate_report(
    body: ReportGenerateIn,
    _: User = Depends(require_roles("admin", "manager")),
    db: Session = Depends(get_db),
):
    """手动触发生成当前周期总结（定时任务之外的管理者兜底入口）。"""
    if body.kind not in ("weekly", "midweek"):
        raise HTTPException(status_code=400, detail="报告类型应为 weekly 或 midweek")
    return generate_period_report(db, body.kind)
