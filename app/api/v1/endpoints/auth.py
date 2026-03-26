from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import create_access_token, get_password_hash, verify_password
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import ChangePasswordInput, LoginInput, Token
from app.api.deps import get_current_user
from app.schemas.user import UserRead

router = APIRouter()


@router.post("/login", response_model=Token)
def login(payload: LoginInput, db: Session = Depends(get_db)):
    # Normaliza email para evitar fallos por mayusculas/espacios en login.
    normalized_email = payload.email.strip().lower()
    user = db.scalar(select(User).where(User.email == normalized_email))
    # Mensaje generico por seguridad: no revelar si fallo email o password.
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales invalidas",
        )
    if not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales invalidas",
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuario inactivo")

    # Este token se usa en el frontend como Bearer para acceder al dashboard y modulos protegidos.
    token = create_access_token(str(user.id))
    return Token(access_token=token, user_id=user.id, role=user.role.value)


@router.post("/change-password")
def change_password(
    payload: ChangePasswordInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Verifica identidad pidiendo password actual antes de permitir el cambio.
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Contrasena actual incorrecta",
        )

    if verify_password(payload.new_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La nueva contrasena no puede ser igual a la actual",
        )

    current_user.hashed_password = get_password_hash(payload.new_password)
    db.add(current_user)
    db.commit()

    return {"ok": True, "message": "Contrasena actualizada"}


@router.get("/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user)):
    # Endpoint util para validar desde frontend si el token sigue vigente.
    return current_user
