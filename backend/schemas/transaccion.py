from pydantic import BaseModel, Field, ConfigDict
from datetime import date, datetime


class TransaccionBase(BaseModel):
    empresa_id: int = Field(..., gt=0)
    sucursal_id: int | None = Field(None, gt=0)
    fecha: date
    cuenta: str = Field(..., min_length=1, max_length=20)
    descripcion: str | None = Field(None, max_length=255)
    monto: float
    moneda: str = Field(..., min_length=3, max_length=3)
    monto_base: float | None = None
    banco: str | None = Field(None, max_length=80)
    categoria: str | None = Field(None, max_length=80)
    es_intercompany: str = Field("N", pattern="^[SN]$")
    empresa_contraparte_id: int | None = None
    archivo_origen: str | None = Field(None, max_length=255)
    fila_origen: int | None = None


class TransaccionCreate(TransaccionBase):
    pass


class TransaccionResponse(TransaccionBase):
    id: int
    creada_en: datetime

    model_config = ConfigDict(from_attributes=True)