from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class SoftwareBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Nombre del software/paquete")
    vendor: str = Field(default="Autodesk", max_length=100, description="Proveedor")
    description: Optional[str] = Field(None, max_length=500, description="Descripción")
    is_active: bool = Field(True, description="Estado activo")


class SoftwareCreate(SoftwareBase):
    """Schema para crear nuevo software"""
    pass


class SoftwareUpdate(BaseModel):
    """Schema para actualizar software"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    vendor: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None


class SoftwareRead(BaseModel):
    id: int
    name: str
    vendor: str
    description: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SoftwareResponse(SoftwareBase):
    """Schema de respuesta para software"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
