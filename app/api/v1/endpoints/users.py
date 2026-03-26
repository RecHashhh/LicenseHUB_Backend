from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.core.security import get_password_hash
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.services.audit_service import log_action

router = APIRouter()


@router.get("", response_model=list[UserRead])
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return list(db.scalars(select(User)).all())


@router.get("/{user_id}", response_model=UserRead)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    user = db.scalar(select(User).where(User.id == user_id))
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user


@router.post("", response_model=UserRead)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    normalized_email = payload.email.strip().lower()
    exists = db.scalar(select(User).where(User.email == normalized_email))
    if exists:
        raise HTTPException(status_code=400, detail="Email ya registrado")

    user = User(
        full_name=payload.full_name,
        email=normalized_email,
        hashed_password=get_password_hash(payload.password),
        role=payload.role,
        is_active=payload.is_active,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    log_action(db, current_user.id, "CREATE", "users", str(user.id), f"Usuario {user.email}")
    return user


@router.put("/{user_id}", response_model=UserRead)
def update_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    user = db.scalar(select(User).where(User.id == user_id))
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    for field, value in payload.model_dump(exclude_none=True).items():
        if field == "password":
            user.hashed_password = get_password_hash(value)
        elif field == "email":
            user.email = value.strip().lower()
        else:
            setattr(user, field, value)

    db.commit()
    db.refresh(user)
    log_action(db, current_user.id, "UPDATE", "users", str(user.id), "Actualizacion usuario")
    return user


@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    user = db.scalar(select(User).where(User.id == user_id))
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="No puedes eliminar tu propio usuario")

    db.delete(user)
    db.commit()
    log_action(db, current_user.id, "DELETE", "users", str(user_id), "Eliminacion usuario")
    return {"ok": True}
