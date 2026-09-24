from collections import Counter
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import MANAGEMENT_ROLES, get_current_user
from app.db.base import get_db
from app.models import PerformanceReview, Task, User, WorkLog
from app.schemas import MonthlyReviewIn, ReviewOut
from app.services import ai

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post("/monthly-review", response_model=ReviewOut)
def monthly_review(
    body: MonthlyReviewIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    month = body.month
    try:
        y, m = map(int, month.split("-"))
        start = date(y, m, 1)
        end = date(y + (m == 12), m % 12 + 1, 1)
    except ValueError:
        raise HTTPException(status_code=400, detail="月份格式应为 YYYY-MM")

    target_id = body.user_id or user.id
    if user.role not in MANAGEMENT_ROLES:
        target_id = user.id
    target = db.get(User, target_id)
    if target is None:
        raise HTTPException(status_code=404, detail="成员不存在")

    # ── 任务统计 ──
    tasks = db.query(Task).filter(Task.assignee_id == target_id).all()
    status_counter = Counter(t.status for t in tasks)
    task_stats = {
        "total": len(tasks),
        "done": status_counter.get("done", 0),
        "in_progress": status_counter.get("in_progress", 0),
        "todo": status_counter.get("todo", 0),
        "blocked": status_counter.get("blocked", 0),
    }

    # ── 日志统计（当月）──
    logs = (
        db.query(WorkLog)
        .filter(WorkLog.user_id == target_id, WorkLog.log_date >= start, WorkLog.log_date < end)
        .order_by(WorkLog.log_date)
        .all()
    )
    total_hours = 0.0
    parsed_task_count = 0
    samples: list[str] = []
    for log in logs:
        if log.parsed:
            parsed_task_count += len(log.parsed.get("tasks", []))
            for t in log.parsed.get("tasks", []):
                hours = t.get("duration_hours")
                if isinstance(hours, (int, float)):
                    total_hours += hours
        samples.append(f"{log.log_date}：{log.content[:120]}")

    payload = {
        "member": target.name,
        "month": month,
        "task_stats": task_stats,
        "worklog_stats": {
            "log_count": len(logs),
            "parsed_task_count": parsed_task_count,
            "total_hours": round(total_hours, 1),
        },
        "worklog_samples": samples[:10],
    }

    content = ai.monthly_review(payload)
    review = PerformanceReview(user_id=target_id, month=month, content=content)
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


@router.get("/reviews", response_model=list[ReviewOut])
def list_reviews(
    month: str | None = None,
    user_id: int | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(PerformanceReview)
    if user.role not in MANAGEMENT_ROLES:
        q = q.filter(PerformanceReview.user_id == user.id)
    elif user_id:
        q = q.filter(PerformanceReview.user_id == user_id)
    if month:
        q = q.filter(PerformanceReview.month == month)
    return q.order_by(PerformanceReview.created_at.desc()).limit(50).all()
