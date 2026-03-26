from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.db.session import get_db
from app.models.software import Software
from app.models.user import User
from app.schemas.software import SoftwareCreate, SoftwareRead, SoftwareUpdate, SoftwareResponse
from app.services.audit_service import log_action

router = APIRouter()


@router.get("", response_model=list[SoftwareRead])
def list_software(
    is_active: bool = Query(None),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user)
):
    """Listar softwares disponibles"""
    query = select(Software).order_by(Software.name)
    
    if is_active is not None:
        query = query.where(Software.is_active == is_active)
    
    query = query.offset(skip).limit(limit)
    return list(db.scalars(query).all())


@router.get("/{software_id}", response_model=SoftwareRead)
def get_software(
    software_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user)
):
    """Obtener un software por ID"""
    software = db.scalar(select(Software).where(Software.id == software_id))
    if not software:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Software no encontrado")
    return software


@router.post("", response_model=SoftwareRead, status_code=status.HTTP_201_CREATED)
def create_software(
    payload: SoftwareCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Crear nuevo software/paquete"""
    exists = db.scalar(select(Software).where(Software.name == payload.name))
    if exists:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Software ya existe")

    item = Software(
        name=payload.name,
        vendor=payload.vendor,
        description=payload.description,
        is_active=payload.is_active
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    log_action(db, current_user.id, "CREATE", "software", str(item.id), f"Creado: {item.name}")
    return item


@router.put("/{software_id}", response_model=SoftwareRead)
def update_software(
    software_id: int,
    payload: SoftwareUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Actualizar software"""
    software = db.scalar(select(Software).where(Software.id == software_id))
    if not software:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Software no encontrado")
    
    # Validar nombre único si se va a cambiar
    if payload.name and payload.name != software.name:
        exists = db.scalar(select(Software).where(Software.name == payload.name))
        if exists:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nombre ya existe")
    
    # Actualizar campos
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(software, key, value)
    
    db.commit()
    db.refresh(software)
    log_action(db, current_user.id, "UPDATE", "software", str(software.id), f"Actualizado: {software.name}")
    return software


@router.delete("/{software_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_software(
    software_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Eliminar software"""
    software = db.scalar(select(Software).where(Software.id == software_id))
    if not software:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Software no encontrado")
    
    db.delete(software)
    db.commit()
    log_action(db, current_user.id, "DELETE", "software", str(software_id), f"Eliminado: {software.name}")

