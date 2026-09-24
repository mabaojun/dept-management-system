from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.core.security import hash_password
from app.db.base import get_db
from app.models import PerformanceReview, Task, User, WorkLog
from app.schemas import ResetPasswordIn, UserCreate, UserOut

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserOut])
def list_users(
    _: User = Depends(require_roles("admin", "manager")),
    db: Session = Depends(get_db),
):
    return db.query(User).order_by(User.id).all()


@router.post("", response_model=UserOut, status_code=201)
def create_user(
    body: UserCreate,
    _: User = Depends(require_roles("admin", "manager")),
    db: Session = Depends(get_db),
):
    if body.role not in ("admin", "manager", "staff"):
        raise HTTPException(status_code=400, detail="无效的角色")
    if body.role == "admin" and _.role != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可创建管理员账号")
    if db.query(User).filter(User.username == body.username).first():
        raise HTTPException(status_code=400, detail="用户名已存在")
    user = User(
        username=body.username,
        password_hash=hash_password(body.password),
        name=body.name,
        role=body.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserOut.model_validate(user)


@router.put("/{user_id}/password", status_code=204)
def reset_password(
    user_id: int,
    body: ResetPasswordIn,
    _: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    """管理员重置任意成员密码。"""
    if len(body.new_password) < 6:
        raise HTTPException(status_code=400, detail="新密码至少 6 位")
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    user.password_hash = hash_password(body.new_password)
    db.commit()


@router.delete("/{user_id}", status_code=204)
def delete_user(
    user_id: int,
    current: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    """管理员删除成员。存在关联业务数据时禁止删除，避免孤儿数据。"""
    if current.id == user_id:
        raise HTTPException(status_code=400, detail="不能删除当前登录账号")
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    if (
        db.query(Task)
        .filter(or_(Task.assignee_id == user_id, Task.creator_id == user_id))
        .first()
    ):
        raise HTTPException(status_code=400, detail="该成员名下存在任务，请先转移或删除其任务")
    if db.query(WorkLog).filter(WorkLog.user_id == user_id).first():
        raise HTTPException(status_code=400, detail="该成员存在工作日志记录，无法删除")
    if db.query(PerformanceReview).filter(PerformanceReview.user_id == user_id).first():
        raise HTTPException(status_code=400, detail="该成员存在绩效记录，无法删除")
    db.delete(user)
    db.commit()
