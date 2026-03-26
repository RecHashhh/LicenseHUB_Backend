from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class EnterpriseBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Nombre de la empresa")
    code: str = Field(..., min_length=1, max_length=20, description="Código único de la empresa")
    description: Optional[str] = Field(None, max_length=500, description="Descripción de la empresa")
    is_active: bool = Field(True, description="Estado activo de la empresa")


class EnterpriseCreate(EnterpriseBase):
    """Schema para crear una nueva empresa"""
    pass


class EnterpriseUpdate(BaseModel):
    """Schema para actualizar una empresa"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    code: Optional[str] = Field(None, min_length=1, max_length=20)
    description: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None


class EnterpriseResponse(EnterpriseBase):
    """Schema de respuesta para empresa"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
