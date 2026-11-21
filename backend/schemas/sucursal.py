from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class SucursalBase(BaseModel):
    empresa_id: int = Field(..., gt=0)
    nombre: str = Field(..., min_length=1, max_length=120)
    ciudad: str | None = Field(None, max_length=80)
    activa: bool = True


class SucursalCreate(SucursalBase):
    pass


class SucursalUpdate(BaseModel):
    nombre: str | None = Field(None, min_length=1, max_length=120)
    ciudad: str | None = Field(None, max_length=80)
    activa: bool | None = None


class SucursalResponse(SucursalBase):
    id: int
    creada_en: datetime

    model_config = ConfigDict(from_attributes=True)