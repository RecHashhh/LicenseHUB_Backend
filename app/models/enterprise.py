from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base import Base


class Enterprise(Base):
    """Modelo de Empresa/Dominio para gestionar múltiples organizaciones"""
    
    __tablename__ = "enterprises"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    code = Column(String(20), unique=True, nullable=False)
    description = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    licenses = relationship("License", back_populates="enterprise")
    
    def __repr__(self):
        return f"<Enterprise {self.code} - {self.name}>"
