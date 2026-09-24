from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.core.deps import MANAGEMENT_ROLES, get_current_user
from app.db.base import get_db
from app.models import Task, User, WorkLog
from app.schemas import DashboardSummary

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def summary(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    is_manager = user.role in MANAGEMENT_ROLES

    task_q = db.query(Task)
    log_q = db.query(WorkLog)
    if not is_manager:
        task_q = task_q.filter(Task.assignee_id == user.id)
        log_q = log_q.filter(WorkLog.user_id == user.id)

    tasks = task_q.all()
    by_status = {"todo": 0, "in_progress": 0, "done": 0, "blocked": 0}
    for t in tasks:
        by_status[t.status] = by_status.get(t.status, 0) + 1
    done = by_status["done"]
    total = len(tasks)

    today = date.today()
    month_start = today.replace(day=1)
    worklog_month_count = log_q.filter(WorkLog.log_date >= month_start).count()

    # 近 14 天完成趋势
    trend_start = today - timedelta(days=13)
    trend_q = db.query(Task).filter(Task.completed_at.isnot(None))
    if not is_manager:
        trend_q = trend_q.filter(Task.assignee_id == user.id)
    counter: dict[str, int] = {}
    for t in trend_q:
        d = t.completed_at.date() if hasattr(t.completed_at, "date") else t.completed_at
        if trend_start <= d <= today:
            key = d.isoformat()
            counter[key] = counter.get(key, 0) + 1
    completion_trend = [
        {"date": (trend_start + timedelta(days=i)).isoformat(), "count": counter.get((trend_start + timedelta(days=i)).isoformat(), 0)}
        for i in range(14)
    ]

    # 成员负载（仅管理侧）
    member_load: list[dict] = []
    if is_manager:
        rows = (
            db.query(
                User.id,
                User.name,
                func.count(Task.id).label("total"),
                func.sum(case((Task.status == "done", 1), else_=0)).label("done"),
            )
            .outerjoin(Task, Task.assignee_id == User.id)
            .group_by(User.id, User.name)
            .all()
        )
        member_load = [
            {"user_id": r.id, "name": r.name, "total": r.total, "done": int(r.done or 0)}
            for r in rows
        ]

    recent = task_q.filter(Task.status != "done").order_by(Task.updated_at.desc()).limit(8).all()

    return DashboardSummary(
        task_total=total,
        task_done=done,
        completion_rate=round(done / total, 4) if total else 0.0,
        worklog_month_count=worklog_month_count,
        task_stats=by_status,
        completion_trend=completion_trend,
        member_load=member_load,
        recent_tasks=recent,
    )
