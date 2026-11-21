from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from database.connection import Base


class Sucursal(Base):
    __tablename__ = "sucursales"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False, index=True)
    nombre = Column(String(120), nullable=False)
    ciudad = Column(String(80), nullable=True)
    activa = Column(Boolean, default=True, nullable=False)
    creada_en = Column(DateTime, server_default=func.now(), nullable=False)

    # Relaciones
    empresa = relationship("Empresa", back_populates="sucursales")

    def __repr__(self):
        return f"<Sucursal(id={self.id}, nombre='{self.nombre}', empresa_id={self.empresa_id})>"