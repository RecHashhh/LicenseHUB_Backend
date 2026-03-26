from datetime import date
from io import BytesIO

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, require_admin
from app.db.session import get_db
from app.models.license import License, LicenseStatusEnum
from app.models.software import Software
from app.models.user import User
from app.schemas.license import LicenseCreate, LicenseRead, LicenseUpdate
from app.services.audit_service import log_action
from app.utils.license_status import calculate_status

router = APIRouter()


def _serialize(license_item: License) -> LicenseRead:
    return LicenseRead(
        id=license_item.id,
        cedula=license_item.cedula,
        nombre=license_item.nombre,
        cargo=license_item.cargo,
        proyecto=license_item.proyecto,
        software_id=license_item.software_id,
        correos_personales=license_item.correos_personales,
        email_enviado_fecha=license_item.email_enviado_fecha,
        habilitacion_licencia_fecha=license_item.habilitacion_licencia_fecha,
        vencimiento_licencia_fecha=license_item.vencimiento_licencia_fecha,
        status=license_item.status,
        verificacion_cedula=license_item.verificacion_cedula,
        verificacion_licencia=license_item.verificacion_licencia,
        verificacion_nomina=license_item.verificacion_nomina,
        observaciones=license_item.observaciones,
        created_at=license_item.created_at,
        updated_at=license_item.updated_at,
        software_name=license_item.software.name,
    )


def _base_query(db: Session):
    return db.query(License).options(joinedload(License.software))


@router.get("", response_model=list[LicenseRead])
def list_licenses(
    cedula: str | None = Query(default=None),
    nombre: str | None = Query(default=None),
    software: str | None = Query(default=None),
    status: LicenseStatusEnum | None = Query(default=None),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    rows = _base_query(db).all()

    for item in rows:
        item.status = calculate_status(item.vencimiento_licencia_fecha)
    db.commit()

    filtered = rows
    if cedula:
        filtered = [x for x in filtered if cedula.lower() in x.cedula.lower()]
    if nombre:
        filtered = [x for x in filtered if nombre.lower() in x.nombre.lower()]
    if software:
        filtered = [x for x in filtered if software.lower() in x.software.name.lower()]
    if status:
        filtered = [x for x in filtered if x.status == status]

    return [_serialize(item) for item in filtered]


@router.post("", response_model=LicenseRead)
def create_license(
    payload: LicenseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    software = db.scalar(select(Software).where(Software.id == payload.software_id))
    if not software:
        raise HTTPException(status_code=400, detail="Software invalido")

    existing = db.scalar(select(License).where(License.cedula == payload.cedula))
    if existing:
        raise HTTPException(status_code=400, detail="Cedula ya registrada")

    item = License(
        **payload.model_dump(),
        status=calculate_status(payload.vencimiento_licencia_fecha),
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    item = _base_query(db).where(License.id == item.id).first()
    log_action(db, current_user.id, "CREATE", "licenses", str(item.id), f"Alta {item.cedula} - {item.nombre}")
    return _serialize(item)


@router.put("/{license_id}", response_model=LicenseRead)
def update_license(
    license_id: int,
    payload: LicenseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    item = db.scalar(select(License).where(License.id == license_id))
    if not item:
        raise HTTPException(status_code=404, detail="Licencia no encontrada")

    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(item, field, value)

    item.status = calculate_status(item.vencimiento_licencia_fecha)
    item.updated_at = date.today()
    db.commit()
    item = _base_query(db).where(License.id == item.id).first()
    log_action(db, current_user.id, "UPDATE", "licenses", str(item.id), f"Actualizacion {item.cedula}")
    return _serialize(item)


@router.delete("/{license_id}")
def delete_license(
    license_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    item = db.scalar(select(License).where(License.id == license_id))
    if not item:
        raise HTTPException(status_code=404, detail="Licencia no encontrada")
    db.delete(item)
    db.commit()
    log_action(db, current_user.id, "DELETE", "licenses", str(license_id), f"Baja {item.cedula}")
    return {"ok": True}


@router.post("/import")
def import_licenses(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    if not file.filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Solo se admite .xlsx")

    df = pd.read_excel(file.file)
    created = 0
    errors = []

    for idx, row in df.iterrows():
        try:
            cedula = str(row.get("CEDULA", "")).strip()
            nombre = str(row.get("NOMBRE", "")).strip()
            software_id = int(row.get("software_id", 1))
            enterprise_id = int(row.get("enterprise_id", 1))

            if not cedula or not nombre:
                errors.append(f"Fila {idx + 2}: Falta cedula o nombre")
                continue

            existing = db.scalar(select(License).where(License.cedula == cedula))
            if existing:
                errors.append(f"Fila {idx + 2}: Cedula {cedula} ya existe")
                continue

            item = License(
                cedula=cedula,
                nombre=nombre,
                cargo=str(row.get("CARGO", "")).strip() or None,
                proyecto=str(row.get("PROYECTO", "")).strip() or None,
                enterprise_id=enterprise_id,
                software_id=software_id,
                correos_personales=str(row.get("CORREOS PERSONALES", "")).strip() or None,
                email_enviado_fecha=pd.to_datetime(row.get("FECHA DE ENVIO DE CORREO")).date() if pd.notna(row.get("FECHA DE ENVIO DE CORREO")) else None,
                habilitacion_licencia_fecha=pd.to_datetime(row.get("FECHA DE HABILITACION DE LICENCIA")).date() if pd.notna(row.get("FECHA DE HABILITACION DE LICENCIA")) else None,
                vencimiento_licencia_fecha=pd.to_datetime(row.get("FECHA DE VENCIMIENTO LICENCIA")).date() if pd.notna(row.get("FECHA DE VENCIMIENTO LICENCIA")) else None,
                verificacion_cedula=bool(row.get("VERIFICACIÓN CEDULA", False)),
                verificacion_licencia=bool(row.get("VERIFICACIÓN LICENCIA", False)),
                verificacion_nomina=bool(row.get("VERIFICACION NOMINA", False)),
                observaciones=str(row.get("OBSERVACIONES", "")).strip() or None,
                status=calculate_status(pd.to_datetime(row.get("FECHA DE VENCIMIENTO LICENCIA")).date() if pd.notna(row.get("FECHA DE VENCIMIENTO LICENCIA")) else None),
            )
            db.add(item)
            created += 1
        except Exception as e:
            errors.append(f"Fila {idx + 2}: {str(e)}")

    db.commit()
    log_action(db, current_user.id, "IMPORT", "licenses", "bulk", f"Importadas {created}, Errores: {len(errors)}")
    return {"created": created, "errors": errors}


@router.get("/export")
def export_licenses(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    rows = _base_query(db).all()
    data = []
    for item in rows:
        item.status = calculate_status(item.vencimiento_licencia_fecha)
        data.append(
            {
                "N°": item.id,
                "CEDULA": item.cedula,
                "NOMBRE": item.nombre,
                "CARGO": item.cargo or "",
                "PROYECTO": item.proyecto or "",
                "FECHA DE ENVIO DE CORREO": item.email_enviado_fecha or "",
                "FECHA DE HABILITACION DE LICENCIA": item.habilitacion_licencia_fecha or "",
                "CORREOS PERSONALES": item.correos_personales or "",
                "FECHA DE VENCIMIENTO LICENCIA": item.vencimiento_licencia_fecha or "",
                "SOFTWARE": item.software.name,
                "ESTADO": item.status.value,
                "VERIFICACIÓN CEDULA": item.verificacion_cedula,
                "VERIFICACIÓN LICENCIA": item.verificacion_licencia,
                "OBSERVACIONES": item.observaciones or "",
                "VERIFICACION NOMINA": item.verificacion_nomina,
            }
        )

    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="LICENCIAS")
    output.seek(0)

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=licencias_autodesk.xlsx"},
    )
