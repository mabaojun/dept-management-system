from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import MANAGEMENT_ROLES, get_current_user
from app.db.base import get_db
from app.models import User, WorkLog
from app.schemas import WorkLogCreate, WorkLogOut
from app.services import ai

router = APIRouter(prefix="/worklogs", tags=["worklogs"])


def month_range(month: str) -> tuple[date, date]:
    """YYYY-MM → [当月第一天, 次月第一天)，跨数据库通用。"""
    try:
        y, m = map(int, month.split("-"))
    except ValueError:
        raise HTTPException(status_code=400, detail="月份格式应为 YYYY-MM")
    start = date(y, m, 1)
    end = date(y + (m == 12), m % 12 + 1, 1)
    return start, end


@router.get("", response_model=list[WorkLogOut])
def list_worklogs(
    month: str | None = None,
    user_id: int | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(WorkLog)
    if user.role not in MANAGEMENT_ROLES:
        q = q.filter(WorkLog.user_id == user.id)
    elif user_id:
        q = q.filter(WorkLog.user_id == user_id)
    if month:
        start, end = month_range(month)
        q = q.filter(WorkLog.log_date >= start, WorkLog.log_date < end)
    return q.order_by(WorkLog.log_date.desc(), WorkLog.id.desc()).limit(200).all()


@router.post("", response_model=WorkLogOut, status_code=201)
def create_worklog(
    body: WorkLogCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    log = WorkLog(user_id=user.id, log_date=body.log_date, content=body.content)
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


@router.post("/{log_id}/parse", response_model=WorkLogOut)
def parse_worklog(
    log_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    log = db.get(WorkLog, log_id)
    if log is None:
        raise HTTPException(status_code=404, detail="日志不存在")
    if user.role not in MANAGEMENT_ROLES and log.user_id != user.id:
        raise HTTPException(status_code=403, detail="只能解析自己的日志")
    log.parsed = ai.parse_worklog(log.content)
    db.commit()
    db.refresh(log)
    return log
