from datetime import date, datetime

from sqlalchemy import JSON, Boolean, Date, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(128))
    name: Mapped[str] = mapped_column(String(64))
    # admin=系统管理员 / manager=部门管理者 / staff=部门成员
    role: Mapped[str] = mapped_column(String(16), default="staff")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    assignee_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    creator_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    # low / mid / high / urgent
    priority: Mapped[str] = mapped_column(String(16), default="mid")
    # todo / in_progress / done / blocked
    status: Mapped[str] = mapped_column(String(16), default="todo", index=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    # 已结束任务归档：默认不进任务列表，管理者可重新下发
    archived: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    # 当前进展叙述：负责人在界面上更新
    progress: Mapped[str] = mapped_column(Text, default="")

    changes: Mapped[list["TaskChangeLog"]] = relationship(
        "TaskChangeLog", back_populates="task", cascade="all, delete-orphan"
    )


class TaskChangeLog(Base):
    """任务改动审计：谁在何时把哪个字段从什么改成什么。"""

    __tablename__ = "task_change_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    # 被改动的字段名：title/description/progress/status/priority/assignee_id/due_date
    field: Mapped[str] = mapped_column(String(32))
    old_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    task: Mapped[Task] = relationship("Task", back_populates="changes")


class WorkLog(Base):
    __tablename__ = "worklogs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    log_date: Mapped[date] = mapped_column(Date, index=True)
    content: Mapped[str] = mapped_column(Text)
    # AI 解析后的结构化结果（无则未解析）
    parsed: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class PerformanceReview(Base):
    __tablename__ = "performance_reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    month: Mapped[str] = mapped_column(String(7), index=True)  # YYYY-MM
    content: Mapped[dict] = mapped_column(JSON)  # AI 参考意见
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class PeriodReport(Base):
    """阶段工作总结：每周二/周五 17:00 结合改动日志自动生成。"""

    __tablename__ = "period_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # midweek=周二简报 / weekly=周五周报
    kind: Mapped[str] = mapped_column(String(16), index=True)
    period_start: Mapped[date] = mapped_column(Date)
    period_end: Mapped[date] = mapped_column(Date)
    content: Mapped[dict] = mapped_column(JSON)  # 总结 + 任务进展明细
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class SystemConfig(Base):
    """系统配置（键值对）：DB 中显式设置的项覆盖 .env 默认值。"""

    __tablename__ = "system_configs"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str] = mapped_column(String(512), default="")
