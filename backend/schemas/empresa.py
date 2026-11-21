from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class EmpresaBase(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=120)
    pais: str = Field(..., min_length=1, max_length=60)
    moneda_local: str = Field(..., min_length=3, max_length=3, description="Código ISO: GTQ, USD, EUR, MXN")
    activa: bool = True


class EmpresaCreate(EmpresaBase):
    pass


class EmpresaUpdate(BaseModel):
    nombre: str | None = Field(None, min_length=1, max_length=120)
    pais: str | None = Field(None, min_length=1, max_length=60)
    moneda_local: str | None = Field(None, min_length=3, max_length=3)
    activa: bool | None = None


class EmpresaResponse(EmpresaBase):
    id: int
    creada_en: datetime

    model_config = ConfigDict(from_attributes=True)