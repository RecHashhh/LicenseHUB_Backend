from datetime import datetime

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.license import License, LicenseStatusEnum
from app.models.user import User
from app.services.report_service import build_pdf_report
from app.utils.license_status import calculate_status

router = APIRouter()


@router.get("/pdf")
def report_pdf(
    status: LicenseStatusEnum | None = Query(default=None),
    cedula: str | None = Query(default=None),
    nombre: str | None = Query(default=None),
    software: str | None = Query(default=None),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    rows = db.query(License).options(joinedload(License.software)).all()

    result = []
    for item in rows:
        item.status = calculate_status(item.vencimiento_licencia_fecha)
        if status and item.status != status:
            continue
        if cedula and cedula.lower() not in item.cedula.lower():
            continue
        if nombre and nombre.lower() not in item.nombre.lower():
            continue
        if software and software.lower() not in item.software.name.lower():
            continue
        result.append(item)

    table_rows = [
        [
            item.cedula,
            item.nombre,
            item.cargo or "-",
            item.proyecto or "-",
            item.software.name,
            item.status.value,
            str(item.habilitacion_licencia_fecha) if item.habilitacion_licencia_fecha else "-",
            str(item.vencimiento_licencia_fecha) if item.vencimiento_licencia_fecha else "-",
        ]
        for item in result
    ]

    summary = {
        "total": len(result),
        "active": len([x for x in result if x.status == LicenseStatusEnum.active]),
        "expired": len([x for x in result if x.status == LicenseStatusEnum.expired]),
        "expiring": len([x for x in result if x.status == LicenseStatusEnum.expiring]),
    }
    title = f"Reporte de Licencias Autodesk - {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    pdf_data = build_pdf_report(title, table_rows, summary)

    return StreamingResponse(
        iter([pdf_data]),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=reporte_licencias.pdf"},
    )
