from datetime import date
from io import BytesIO
import unicodedata
import logging

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, require_admin
from app.db.session import get_db
from app.models.enterprise import Enterprise
from app.models.license import License, LicenseStatusEnum
from app.models.software import Software
from app.models.user import User
from app.schemas.license import LicenseCreate, LicenseRead, LicenseUpdate
from app.services.audit_service import log_action
from app.utils.license_status import calculate_status

router = APIRouter()
logger = logging.getLogger(__name__)

REQUIRED_IMPORT_COLUMNS = {"CEDULA", "NOMBRE"}
ACTIVE_LICENSE_STATUSES = {LicenseStatusEnum.active, LicenseStatusEnum.expiring}


def _normalize_header(value) -> str:
    if value is None or pd.isna(value):
        return ""
    text = str(value).replace("\xa0", " ").strip()
    text = " ".join(text.split())
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return text.upper()


def _normalize_dataframe_columns(df: pd.DataFrame) -> pd.DataFrame:
    normalized = df.copy()
    normalized.columns = [_normalize_header(col) for col in normalized.columns]
    return normalized


def _read_excel_with_detected_header(file: UploadFile) -> pd.DataFrame:
    file.file.seek(0)
    df = pd.read_excel(file.file)
    df = _normalize_dataframe_columns(df)

    if REQUIRED_IMPORT_COLUMNS.issubset(set(df.columns)):
        return df

    file.file.seek(0)
    raw = pd.read_excel(file.file, header=None)
    max_rows_to_scan = min(15, len(raw.index))
    header_row = None

    for idx in range(max_rows_to_scan):
        normalized_row = {_normalize_header(v) for v in raw.iloc[idx].tolist()}
        if REQUIRED_IMPORT_COLUMNS.issubset(normalized_row):
            header_row = idx
            break

    if header_row is None:
        detected = [str(col) for col in df.columns if str(col)]
        raise HTTPException(
            status_code=400,
            detail=(
                "Columnas requeridas faltantes: CEDULA, NOMBRE. "
                f"Encabezados detectados: {', '.join(detected) if detected else 'ninguno'}"
            ),
        )

    headers = raw.iloc[header_row].tolist()
    data = raw.iloc[header_row + 1 :].copy()
    data.columns = headers
    data = _normalize_dataframe_columns(data)
    return data


def _is_empty(value) -> bool:
    return value is None or pd.isna(value) or str(value).strip() == ""


def _to_clean_str(value) -> str | None:
    if _is_empty(value):
        return None
    return str(value).strip()


def _to_cedula(value) -> str:
    if _is_empty(value):
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def _to_int_or_default(value, default: int) -> int:
    if _is_empty(value):
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    text = str(value).strip()
    try:
        return int(text)
    except ValueError:
        return int(float(text))


def _to_bool(value, default: bool = False) -> bool:
    if _is_empty(value):
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return int(value) == 1

    text = str(value).strip().lower()
    true_values = {"1", "true", "si", "sí", "yes", "y"}
    false_values = {"0", "false", "no", "n"}

    if text in true_values:
        return True
    if text in false_values:
        return False
    raise ValueError(f"Valor booleano invalido: {value}")


def _to_date(value):
    if _is_empty(value):
        return None
    return pd.to_datetime(value).date()


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

    new_status = calculate_status(payload.vencimiento_licencia_fecha)
    if new_status in ACTIVE_LICENSE_STATUSES:
        existing_active = db.scalar(
            select(License.id).where(
                License.cedula == payload.cedula,
                License.software_id == payload.software_id,
                License.enterprise_id == 1,
                License.status.in_(ACTIVE_LICENSE_STATUSES),
            )
        )
        if existing_active:
            raise HTTPException(
                status_code=400,
                detail="El usuario ya tiene una licencia activa para este software",
            )

    item = License(
        **payload.model_dump(),
        status=new_status,
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

    df = _read_excel_with_detected_header(file)

    created = 0
    errors = []
    existing_active_keys = set(
        db.execute(
            select(License.cedula, License.software_id, License.enterprise_id).where(
                License.status.in_(ACTIVE_LICENSE_STATUSES)
            )
        ).all()
    )
    batch_active_keys = set()

    for idx, row in df.iterrows():
        try:
            cedula = _to_cedula(row.get("CEDULA"))
            nombre = _to_clean_str(row.get("NOMBRE")) or ""
            software_id = _to_int_or_default(row.get("SOFTWARE_ID"), 1)
            enterprise_id = _to_int_or_default(row.get("ENTERPRISE_ID"), 1)

            if not cedula or not nombre:
                errors.append(f"Fila {idx + 2}: Falta cedula o nombre")
                continue

            software = db.scalar(select(Software).where(Software.id == software_id))
            if not software:
                errors.append(f"Fila {idx + 2}: software_id {software_id} no existe")
                continue

            enterprise_exists = db.scalar(select(Enterprise.id).where(Enterprise.id == enterprise_id))
            if not enterprise_exists:
                errors.append(f"Fila {idx + 2}: enterprise_id {enterprise_id} no existe")
                continue

            status = calculate_status(_to_date(row.get("FECHA DE VENCIMIENTO LICENCIA")))
            active_key = (cedula, software_id, enterprise_id)
            if status in ACTIVE_LICENSE_STATUSES and (
                active_key in existing_active_keys or active_key in batch_active_keys
            ):
                errors.append(
                    f"Fila {idx + 2}: {nombre} ya tiene una licencia activa para software {software.name}"
                )
                continue

            item = License(
                cedula=cedula,
                nombre=nombre,
                cargo=_to_clean_str(row.get("CARGO")),
                proyecto=_to_clean_str(row.get("PROYECTO")),
                enterprise_id=enterprise_id,
                software_id=software_id,
                correos_personales=_to_clean_str(row.get("CORREOS PERSONALES")),
                email_enviado_fecha=_to_date(row.get("FECHA DE ENVIO DE CORREO")),
                habilitacion_licencia_fecha=_to_date(row.get("FECHA DE HABILITACION DE LICENCIA")),
                vencimiento_licencia_fecha=_to_date(row.get("FECHA DE VENCIMIENTO LICENCIA")),
                verificacion_cedula=_to_bool(row.get("VERIFICACION CEDULA", False)),
                verificacion_licencia=_to_bool(row.get("VERIFICACION LICENCIA", False)),
                verificacion_nomina=_to_bool(row.get("VERIFICACION NOMINA", False)),
                observaciones=_to_clean_str(row.get("OBSERVACIONES")),
                status=status,
            )
            db.add(item)
            if status in ACTIVE_LICENSE_STATUSES:
                batch_active_keys.add(active_key)
            created += 1
        except Exception as e:
            errors.append(f"Fila {idx + 2}: {str(e)}")

    if errors:
        logger.warning("Importacion de licencias con errores (%s):", len(errors))
        for err in errors:
            logger.warning(err)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Conflicto de integridad al importar. Verifica duplicados y restricciones de base de datos.",
        )

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
