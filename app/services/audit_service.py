from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def log_action(
    db: Session,
    user_id: int,
    action: str,
    entity: str,
    entity_id: str,
    details: str | None = None,
) -> None:
    item = AuditLog(
        user_id=user_id,
        action=action,
        entity=entity,
        entity_id=entity_id,
        details=details,
    )
    db.add(item)
    db.commit()
