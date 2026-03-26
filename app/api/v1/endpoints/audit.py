from fastapi import APIRouter, Depends
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.db.session import get_db
from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.audit import AuditRead

router = APIRouter()


@router.get("", response_model=list[AuditRead])
def list_audit_logs(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return list(db.scalars(select(AuditLog).order_by(desc(AuditLog.created_at))).all())
