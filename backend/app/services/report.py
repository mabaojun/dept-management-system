"""阶段工作总结生成：结合任务快照与周期内改动日志。

- weekly（周五 17:00）：本周一 → 今天
- midweek（周二 17:00）：上周六 → 今天
- 未配置 LLM Key 时由 ai.period_report 降级为规则拼接
"""
from datetime import date, datetime, time

from sqlalchemy.orm import Session

from app.models import PeriodReport, Task, TaskChangeLog, User
from app.services import ai

# 改动记录中的字段中文名（与 api/tasks.py 保持一致）
FIELD_LABELS = {
    "title": "标题",
    "description": "任务详情",
    "progress": "进展叙述",
    "assignee_id": "负责人",
    "priority": "优先级",
    "status": "状态",
    "due_date": "截止日期",
}


def period_window(kind: str, today: date | None = None) -> tuple[date, date]:
    """按报告类型推算覆盖窗口 [start, end]。"""
    today = today or date.today()
    weekday = today.weekday()  # 周一=0
    if kind == "weekly":
        start = today.fromordinal(today.toordinal() - weekday)  # 本周一
    elif kind == "midweek":
        start = today.fromordinal(today.toordinal() - weekday - 3)  # 上周六
    else:
        raise ValueError(f"未知报告类型: {kind}")
    return start, today


def _collect_payload(db: Session, start: date, end: date) -> dict:
    tasks = db.query(Task).filter(Task.archived.is_(False)).all()
    names = {u.id: u.name for u in db.query(User).all()}

    task_items = [
        {
            "title": t.title,
            "assignee": names.get(t.assignee_id, str(t.assignee_id)),
            "status": t.status,
            "progress": t.progress or "",
            "due_date": t.due_date.isoformat() if t.due_date else None,
        }
        for t in tasks
    ]

    start_dt = datetime.combine(start, time.min)
    end_dt = datetime.combine(end, time.max)
    changes = (
        db.query(TaskChangeLog)
        .filter(TaskChangeLog.created_at >= start_dt, TaskChangeLog.created_at <= end_dt)
        .order_by(TaskChangeLog.created_at.desc())
        .limit(100)
        .all()
    )
    title_map = {t.id: t.title for t in tasks}
    change_items = [
        {
            "time": c.created_at.isoformat(sep=" ", timespec="minutes"),
            "task": title_map.get(c.task_id, f"任务#{c.task_id}"),
            "user": names.get(c.user_id, str(c.user_id)),
            "field": FIELD_LABELS.get(c.field, c.field),
            "old": c.old_value,
            "new": c.new_value,
        }
        for c in changes
    ]
    return {
        "period_start": start.isoformat(),
        "period_end": end.isoformat(),
        "tasks": task_items,
        "changes": change_items,
    }


def generate_period_report(db: Session, kind: str) -> PeriodReport:
    """生成并落库一份阶段工作总结。"""
    start, end = period_window(kind)
    payload = _collect_payload(db, start, end)
    result = ai.period_report(payload)
    content = {
        "summary": result.get("summary", ""),
        "highlights": result.get("highlights", []),
        "risks": result.get("risks", []),
        "task_count": len(payload["tasks"]),
        "change_count": len(payload["changes"]),
        "tasks": payload["tasks"],
    }
    report = PeriodReport(kind=kind, period_start=start, period_end=end, content=content)
    db.add(report)
    db.commit()
    db.refresh(report)
    return report
