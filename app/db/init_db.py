from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.software import Software
from app.models.user import RoleEnum, User


def seed_admin_user(db: Session) -> None:
    statement = select(User).where(User.email == "admin@empresa.com")
    user = db.scalar(statement)
    if user:
        return

    admin = User(
        full_name="Administrador",
        email="admin@empresa.com",
        hashed_password=get_password_hash("Admin123*"),
        role=RoleEnum.admin,
        is_active=True,
    )
    db.add(admin)
    db.commit()


def seed_software_catalog(db: Session) -> None:
    default_items = ["AutoCAD", "Revit", "Civil 3D", "Navisworks", "BIM 360"]
    existing_names = {item.name for item in db.scalars(select(Software)).all()}

    for name in default_items:
        if name in existing_names:
            continue
        db.add(Software(name=name, vendor="Autodesk"))

    db.commit()
