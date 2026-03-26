from datetime import datetime
from sqlalchemy import Integer, String, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Software(Base):
    __tablename__ = "software"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    vendor: Mapped[str] = mapped_column(String(100), default="Autodesk")
    description: Mapped[str] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    licenses: Mapped[list["License"]] = relationship("License", back_populates="software")
    requests: Mapped[list["LicenseRequest"]] = relationship("LicenseRequest", back_populates="software")
    
    def __repr__(self):
        return f"<Software {self.name} - {self.vendor}>"
