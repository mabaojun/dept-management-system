from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


# ── Auth / Users ──
class LoginIn(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    name: str
    role: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class UserCreate(BaseModel):
    username: str
    password: str
    name: str
    role: str = "staff"


class ChangePasswordIn(BaseModel):
    old_password: str
    new_password: str


class ResetPasswordIn(BaseModel):
    new_password: str


# ── AI 配置 ──
class AiConfigOut(BaseModel):
    base_url: str
    model: str
    api_key_set: bool
    api_key_tail: str  # 密钥末 4 位，用于确认已配置
    mock_mode: bool


class AiConfigIn(BaseModel):
    base_url: str | None = None  # None=保持不变
    model: str | None = None
    api_key: str | None = None  # None=保持不变，空串=清除


# ── Tasks ──
class TaskCreate(BaseModel):
    title: str
    description: str = ""
    assignee_id: int
    priority: str = "mid"
    due_date: date | None = None


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    progress: str | None = None  # 当前进展叙述
    assignee_id: int | None = None
    priority: str | None = None
    status: str | None = None
    due_date: date | None = None


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    progress: str
    assignee_id: int
    creator_id: int
    priority: str
    status: str
    due_date: date | None
    created_at: datetime
    completed_at: datetime | None
    archived: bool


class TaskChangeLogOut(BaseModel):
    id: int
    task_id: int
    user_id: int
    user_name: str
    field: str
    old_value: str | None
    new_value: str | None
    created_at: datetime


# ── WorkLogs ──
class WorkLogCreate(BaseModel):
    log_date: date
    content: str


class WorkLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    log_date: date
    content: str
    parsed: dict[str, Any] | None
    created_at: datetime


# ── Analysis ──
class MonthlyReviewIn(BaseModel):
    month: str  # YYYY-MM
    user_id: int | None = None


class ReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    month: str
    content: dict[str, Any]
    created_at: datetime


# ── 阶段工作总结 ──
class ReportGenerateIn(BaseModel):
    # weekly=周五周报（本周一至今） / midweek=周二简报（上周六至今）
    kind: str = "weekly"


class PeriodReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    kind: str
    period_start: date
    period_end: date
    content: dict[str, Any]
    created_at: datetime


# ── Dashboard ──
class DashboardSummary(BaseModel):
    task_total: int
    task_done: int
    completion_rate: float
    worklog_month_count: int
    task_stats: dict[str, int]
    completion_trend: list[dict[str, Any]]
    member_load: list[dict[str, Any]]
    recent_tasks: list[TaskOut]
