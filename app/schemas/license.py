from datetime import date, datetime

from pydantic import BaseModel

from app.models.license import LicenseStatusEnum


class LicenseBase(BaseModel):
    cedula: str
    nombre: str
    cargo: str | None = None
    proyecto: str | None = None
    software_id: int
    correos_personales: str | None = None
    email_enviado_fecha: date | None = None
    habilitacion_licencia_fecha: date | None = None
    vencimiento_licencia_fecha: date | None = None
    verificacion_cedula: bool = False
    verificacion_licencia: bool = False
    verificacion_nomina: bool = False
    observaciones: str | None = None


class LicenseCreate(LicenseBase):
    pass


class LicenseUpdate(BaseModel):
    cedula: str | None = None
    nombre: str | None = None
    cargo: str | None = None
    proyecto: str | None = None
    software_id: int | None = None
    correos_personales: str | None = None
    email_enviado_fecha: date | None = None
    habilitacion_licencia_fecha: date | None = None
    vencimiento_licencia_fecha: date | None = None
    verificacion_cedula: bool | None = None
    verificacion_licencia: bool | None = None
    verificacion_nomina: bool | None = None
    observaciones: str | None = None


class LicenseRead(LicenseBase):
    id: int
    status: LicenseStatusEnum
    created_at: datetime
    updated_at: datetime
    software_name: str

    model_config = {"from_attributes": True}
