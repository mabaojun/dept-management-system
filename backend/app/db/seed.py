from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import hash_password
from app.models import User


def seed_admin(db: Session) -> None:
    settings = get_settings()
    exists = db.query(User).filter(User.role == "admin").first()
    if exists is not None:
        return
    admin = User(
        username=settings.ADMIN_USERNAME,
        password_hash=hash_password(settings.ADMIN_PASSWORD),
        name=settings.ADMIN_NAME,
        role="admin",
    )
    db.add(admin)
    db.commit()
