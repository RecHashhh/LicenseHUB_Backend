from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, require_admin
from app.db.session import get_db
from app.models.license_request import LicenseRequest
from app.models.software import Software
from app.models.user import RoleEnum, User
from app.schemas.request import RequestCreate, RequestRead, RequestUpdateStatus
from app.services.audit_service import log_action

router = APIRouter()


@router.get("", response_model=list[RequestRead])
def list_requests(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    rows = (
        db.query(LicenseRequest)
        .options(joinedload(LicenseRequest.software), joinedload(LicenseRequest.request_user))
        .all()
    )
    return [
        RequestRead(
            id=item.id,
            request_type=item.request_type,
            status=item.status,
            user_id=item.user_id,
            software_id=item.software_id,
            project_name=item.project_name,
            justification=item.justification,
            required_date=item.required_date,
            payment_method=item.payment_method,
            contact_info=item.contact_info,
            process_owner=item.process_owner,
            created_at=item.created_at,
            software_name=item.software.name,
            user_name=item.request_user.full_name,
        )
        for item in rows
    ]


@router.post("", response_model=RequestRead)
def create_request(
    payload: RequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != RoleEnum.admin and payload.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Solo puedes crear solicitudes para tu usuario")

    software = db.scalar(select(Software).where(Software.id == payload.software_id))
    user = db.scalar(select(User).where(User.id == payload.user_id))
    if not software or not user:
        raise HTTPException(status_code=400, detail="Software o usuario invalido")

    item = LicenseRequest(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)

    row = (
        db.query(LicenseRequest)
        .options(joinedload(LicenseRequest.software), joinedload(LicenseRequest.request_user))
        .where(LicenseRequest.id == item.id)
        .first()
    )
    log_action(db, current_user.id, "CREATE", "requests", str(item.id), "Nueva solicitud")

    return RequestRead(
        id=row.id,
        request_type=row.request_type,
        status=row.status,
        user_id=row.user_id,
        software_id=row.software_id,
        project_name=row.project_name,
        justification=row.justification,
        required_date=row.required_date,
        payment_method=row.payment_method,
        contact_info=row.contact_info,
        process_owner=row.process_owner,
        created_at=row.created_at,
        software_name=row.software.name,
        user_name=row.request_user.full_name,
    )


@router.patch("/{request_id}/status", response_model=RequestRead)
def update_request_status(
    request_id: int,
    payload: RequestUpdateStatus,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    item = db.scalar(select(LicenseRequest).where(LicenseRequest.id == request_id))
    if not item:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    item.status = payload.status
    db.commit()

    row = (
        db.query(LicenseRequest)
        .options(joinedload(LicenseRequest.software), joinedload(LicenseRequest.request_user))
        .where(LicenseRequest.id == item.id)
        .first()
    )
    log_action(db, current_user.id, "UPDATE", "requests", str(item.id), f"Estado {item.status.value}")

    return RequestRead(
        id=row.id,
        request_type=row.request_type,
        status=row.status,
        user_id=row.user_id,
        software_id=row.software_id,
        project_name=row.project_name,
        justification=row.justification,
        required_date=row.required_date,
        payment_method=row.payment_method,
        contact_info=row.contact_info,
        process_owner=row.process_owner,
        created_at=row.created_at,
        software_name=row.software.name,
        user_name=row.request_user.full_name,
    )
