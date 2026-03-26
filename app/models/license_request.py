import enum
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class RequestTypeEnum(str, enum.Enum):
    new = "Nueva licencia"
    renewal = "Renovacion"


class RequestStatusEnum(str, enum.Enum):
    pending = "Pendiente"
    approved = "Aprobada"
    rejected = "Rechazada"


class LicenseRequest(Base):
    __tablename__ = "requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    request_type: Mapped[RequestTypeEnum] = mapped_column(Enum(RequestTypeEnum), nullable=False)
    status: Mapped[RequestStatusEnum] = mapped_column(
        Enum(RequestStatusEnum), default=RequestStatusEnum.pending, nullable=False
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    software_id: Mapped[int] = mapped_column(ForeignKey("software.id"), nullable=False)
    project_name: Mapped[str] = mapped_column(String(120), nullable=False)
    justification: Mapped[str] = mapped_column(Text, nullable=False)
    required_date: Mapped[date] = mapped_column(Date, nullable=False)
    payment_method: Mapped[str] = mapped_column(String(80), nullable=True)
    contact_info: Mapped[str] = mapped_column(String(180), nullable=True)
    process_owner: Mapped[str] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    request_user: Mapped["User"] = relationship("User", back_populates="requests")
    software: Mapped["Software"] = relationship("Software", back_populates="requests")
