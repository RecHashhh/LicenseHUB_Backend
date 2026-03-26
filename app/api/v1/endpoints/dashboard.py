from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.license import License, LicenseStatusEnum
from app.models.user import User
from app.schemas.dashboard import DashboardSummary
from app.utils.license_status import calculate_status

router = APIRouter()


@router.get("/summary", response_model=DashboardSummary)
def get_summary(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    rows = list(db.scalars(select(License)).all())
    for item in rows:
        item.status = calculate_status(item.vencimiento_licencia_fecha)
    db.commit()

    total = len(rows)
    active = len([x for x in rows if x.status == LicenseStatusEnum.active])
    expired = len([x for x in rows if x.status == LicenseStatusEnum.expired])
    expiring = len([x for x in rows if x.status == LicenseStatusEnum.expiring])

    return DashboardSummary(
        total_licenses=total,
        active_licenses=active,
        expired_licenses=expired,
        expiring_licenses=expiring,
    )
