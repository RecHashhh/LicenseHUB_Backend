import enum
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class LicenseStatusEnum(str, enum.Enum):
    active = "Activa"
    expired = "Vencida"
    expiring = "Proxima a vencer"


class License(Base):
    __tablename__ = "licenses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    cedula: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    cargo: Mapped[str] = mapped_column(String(100), nullable=True)
    proyecto: Mapped[str] = mapped_column(String(150), nullable=True)
    software_id: Mapped[int] = mapped_column(ForeignKey("software.id"), nullable=False)
    enterprise_id: Mapped[int] = mapped_column(ForeignKey("enterprises.id"), nullable=False, default=1)
    correos_personales: Mapped[str] = mapped_column(String(200), nullable=True)
    email_enviado_fecha: Mapped[date] = mapped_column(Date, nullable=True)
    habilitacion_licencia_fecha: Mapped[date] = mapped_column(Date, nullable=True)
    vencimiento_licencia_fecha: Mapped[date] = mapped_column(Date, nullable=True)
    status: Mapped[LicenseStatusEnum] = mapped_column(
        Enum(LicenseStatusEnum), default=LicenseStatusEnum.active, nullable=False
    )
    verificacion_cedula: Mapped[bool] = mapped_column(Boolean, default=False)
    verificacion_licencia: Mapped[bool] = mapped_column(Boolean, default=False)
    verificacion_nomina: Mapped[bool] = mapped_column(Boolean, default=False)
    observaciones: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    software: Mapped["Software"] = relationship("Software", back_populates="licenses")
    enterprise: Mapped["Enterprise"] = relationship("Enterprise", back_populates="licenses")
