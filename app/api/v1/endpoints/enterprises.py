from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_admin, get_current_user
from app.models.enterprise import Enterprise
from app.models.user import User
from app.schemas.enterprise import (
    EnterpriseCreate, 
    EnterpriseUpdate, 
    EnterpriseResponse
)
from app.services.audit_service import log_action

router = APIRouter(tags=["enterprises"])


@router.get("/", response_model=list[EnterpriseResponse])
def list_enterprises(
    skip: int = 0,
    limit: int = 100,
    is_active: bool = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Listar todas las empresas.
    
    - **skip**: Número de registros a saltar
    - **limit**: Número máximo de registros a retornar
    - **is_active**: Filtrar por estado activo (opcional)
    """
    query = select(Enterprise)
    
    if is_active is not None:
        query = query.where(Enterprise.is_active == is_active)
    
    # MSSQL requiere ORDER BY cuando se usa OFFSET/LIMIT
    query = query.order_by(Enterprise.id).offset(skip).limit(limit)
    enterprises = db.scalars(query).all()
    return enterprises


@router.get("/{enterprise_id}", response_model=EnterpriseResponse)
def get_enterprise(
    enterprise_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Obtener una empresa por ID"""
    enterprise = db.scalar(select(Enterprise).where(Enterprise.id == enterprise_id))
    if not enterprise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Empresa con ID {enterprise_id} no encontrada"
        )
    return enterprise


@router.post("/", response_model=EnterpriseResponse, status_code=status.HTTP_201_CREATED)
def create_enterprise(
    data: EnterpriseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Crear una nueva empresa.
    
    Solo usuarios con rol admin pueden crear empresas.
    """
    # Verificar código único
    existing_code = db.scalar(select(Enterprise).where(Enterprise.code == data.code))
    if existing_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Código de empresa '{data.code}' ya existe"
        )
    
    # Verificar nombre único
    existing_name = db.scalar(select(Enterprise).where(Enterprise.name == data.name))
    if existing_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Empresa con nombre '{data.name}' ya existe"
        )
    
    enterprise = Enterprise(**data.dict())
    db.add(enterprise)
    db.commit()
    db.refresh(enterprise)
    
    log_action(
        db,
        current_user.id,
        "CREATE",
        "enterprises",
        str(enterprise.id),
        f"Empresa creada: {enterprise.name}"
    )
    
    return enterprise


@router.put("/{enterprise_id}", response_model=EnterpriseResponse)
def update_enterprise(
    enterprise_id: int,
    data: EnterpriseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Actualizar una empresa.
    
    Solo usuarios con rol admin pueden actualizar empresas.
    """
    enterprise = db.scalar(select(Enterprise).where(Enterprise.id == enterprise_id))
    if not enterprise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Empresa con ID {enterprise_id} no encontrada"
        )
    
    # Validar código único si se va a cambiar
    if data.code and data.code != enterprise.code:
        existing = db.scalar(select(Enterprise).where(Enterprise.code == data.code))
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Código '{data.code}' ya existe"
            )
    
    # Validar nombre único si se va a cambiar
    if data.name and data.name != enterprise.name:
        existing = db.scalar(select(Enterprise).where(Enterprise.name == data.name))
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Nombre '{data.name}' ya existe"
            )
    
    # Actualizar campos
    for key, value in data.dict(exclude_unset=True).items():
        setattr(enterprise, key, value)
    
    db.commit()
    db.refresh(enterprise)
    
    log_action(
        db,
        current_user.id,
        "UPDATE",
        "enterprises",
        str(enterprise.id),
        f"Empresa actualizada: {enterprise.name}"
    )
    
    return enterprise


@router.delete("/{enterprise_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_enterprise(
    enterprise_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Eliminar una empresa.
    
    Solo usuarios con rol admin pueden eliminar empresas.
    """
    enterprise = db.scalar(select(Enterprise).where(Enterprise.id == enterprise_id))
    if not enterprise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Empresa con ID {enterprise_id} no encontrada"
        )
    
    # Verificar si hay licencias asociadas
    license_count = db.scalar(
        select(func.count(1)).select_from(Enterprise.__table__)
        .outerjoin(Enterprise.licenses)
        .where(Enterprise.id == enterprise_id)
    )
    
    if license_count and license_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede eliminar empresa con licencias asociadas. Elimina primero las licencias."
        )
    
    db.delete(enterprise)
    db.commit()
    
    log_action(
        db,
        current_user.id,
        "DELETE",
        "enterprises",
        str(enterprise_id),
        f"Empresa eliminada: {enterprise.name}"
    )
