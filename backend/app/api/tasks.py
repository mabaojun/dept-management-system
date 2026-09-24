from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import MANAGEMENT_ROLES, get_current_user, require_roles
from app.db.base import get_db
from app.models import Task, TaskChangeLog, User
from app.schemas import TaskChangeLogOut, TaskCreate, TaskOut, TaskUpdate

router = APIRouter(prefix="/tasks", tags=["tasks"])

VALID_STATUS = ("todo", "in_progress", "done", "blocked")
VALID_PRIORITY = ("low", "mid", "high", "urgent")

# 改动记录中的字段中文名
FIELD_LABELS = {
    "title": "标题",
    "description": "任务详情",
    "progress": "进展叙述",
    "assignee_id": "负责人",
    "priority": "优先级",
    "status": "状态",
    "due_date": "截止日期",
}

# 成员（非管理侧）可自行维护的字段：状态 + 详情 + 进展叙述
STAFF_EDITABLE_FIELDS = ("status", "description", "progress")


def _scope_query(user: User, db: Session):
    """成员只能看到分配给自己的任务；管理侧可见全部。"""
    q = db.query(Task)
    if user.role not in MANAGEMENT_ROLES:
        q = q.filter(Task.assignee_id == user.id)
    return q


@router.get("", response_model=list[TaskOut])
def list_tasks(
    status: str | None = None,
    assignee_id: int | None = None,
    archived: bool = False,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """archived=False 返回进行中清单，archived=True 查看存档。"""
    q = _scope_query(user, db).filter(Task.archived == archived)
    if status:
        q = q.filter(Task.status == status)
    if assignee_id and user.role in MANAGEMENT_ROLES:
        q = q.filter(Task.assignee_id == assignee_id)
    return q.order_by(Task.updated_at.desc()).all()


@router.post("", response_model=TaskOut, status_code=201)
def create_task(
    body: TaskCreate,
    user: User = Depends(require_roles("admin", "manager")),
    db: Session = Depends(get_db),
):
    if body.priority not in VALID_PRIORITY:
        raise HTTPException(status_code=400, detail="无效的优先级")
    assignee = db.get(User, body.assignee_id)
    if assignee is None:
        raise HTTPException(status_code=400, detail="负责人不存在")
    task = Task(**body.model_dump(), creator_id=user.id)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.patch("/{task_id}", response_model=TaskOut)
def update_task(
    task_id: int,
    body: TaskUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="任务不存在")
    is_manager = user.role in MANAGEMENT_ROLES
    if not is_manager and task.assignee_id != user.id:
        raise HTTPException(status_code=403, detail="只能操作自己的任务")

    changes = body.model_dump(exclude_unset=True)
    if not is_manager:
        # 成员可维护：状态、任务详情、进展叙述
        changes = {k: v for k, v in changes.items() if k in STAFF_EDITABLE_FIELDS}
    if "priority" in changes and changes["priority"] not in VALID_PRIORITY:
        raise HTTPException(status_code=400, detail="无效的优先级")
    if "status" in changes:
        if changes["status"] not in VALID_STATUS:
            raise HTTPException(status_code=400, detail="无效的状态")
        if changes["status"] == "done" and task.status != "done":
            task.completed_at = datetime.now(timezone.utc)
        elif changes["status"] != "done":
            task.completed_at = None

    # 审计：逐字段比对旧值，有实际变化才记录
    logs = []
    for k, v in changes.items():
        old = getattr(task, k)
        if _fmt(old) != _fmt(v):
            logs.append(
                TaskChangeLog(
                    task_id=task.id,
                    user_id=user.id,
                    field=k,
                    old_value=_fmt(old),
                    new_value=_fmt(v),
                )
            )
    for k, v in changes.items():
        setattr(task, k, v)
    db.add_all(logs)
    db.commit()
    db.refresh(task)
    return task


def _fmt(v: object) -> str:
    """统一转字符串比对/存储，None 视为空串。"""
    return "" if v is None else str(v)


@router.get("/{task_id}/changes", response_model=list[TaskChangeLogOut])
def list_task_changes(
    task_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """任务改动记录（审计日志）。"""
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="任务不存在")
    if user.role not in MANAGEMENT_ROLES and task.assignee_id != user.id:
        raise HTTPException(status_code=403, detail="只能查看自己任务的改动记录")
    rows = (
        db.query(TaskChangeLog)
        .filter(TaskChangeLog.task_id == task_id)
        .order_by(TaskChangeLog.created_at.desc(), TaskChangeLog.id.desc())
        .limit(100)
        .all()
    )
    names = {u.id: u.name for u in db.query(User).all()}
    return [
        TaskChangeLogOut(
            id=r.id,
            task_id=r.task_id,
            user_id=r.user_id,
            user_name=names.get(r.user_id, str(r.user_id)),
            field=r.field,
            old_value=r.old_value,
            new_value=r.new_value,
            created_at=r.created_at,
        )
        for r in rows
    ]


@router.delete("/{task_id}", status_code=204)
def delete_task(
    task_id: int,
    user: User = Depends(require_roles("admin", "manager")),
    db: Session = Depends(get_db),
):
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="任务不存在")
    db.delete(task)
    db.commit()


@router.post("/{task_id}/archive", response_model=TaskOut)
def archive_task(
    task_id: int,
    _: User = Depends(require_roles("admin", "manager")),
    db: Session = Depends(get_db),
):
    """已结束任务存档：从主清单移入存档区。"""
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="任务不存在")
    if task.status != "done":
        raise HTTPException(status_code=400, detail="仅已完成的任务可存档")
    task.archived = True
    db.commit()
    db.refresh(task)
    return task


@router.post("/{task_id}/reopen", response_model=TaskOut)
def reopen_task(
    task_id: int,
    _: User = Depends(require_roles("admin", "manager")),
    db: Session = Depends(get_db),
):
    """重新下发：存档任务恢复为待开始，回到主任务清单。"""
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="任务不存在")
    if not task.archived:
        raise HTTPException(status_code=400, detail="该任务不在存档中")
    task.archived = False
    task.status = "todo"
    task.completed_at = None
    db.commit()
    db.refresh(task)
    return task
