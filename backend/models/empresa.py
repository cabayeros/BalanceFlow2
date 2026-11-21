from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from sqlalchemy.orm import relationship
from database.connection import Base


class Empresa(Base):
    __tablename__ = "empresas"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(120), nullable=False)
    pais = Column(String(60), nullable=False)
    moneda_local = Column(String(3), nullable=False)  # GTQ, USD, EUR, MXN
    activa = Column(Boolean, default=True, nullable=False)
    creada_en = Column(DateTime, server_default=func.now(), nullable=False)

    # Relaciones
    sucursales = relationship(
        "Sucursal",
        back_populates="empresa",
        cascade="all, delete-orphan",
    )
    transacciones = relationship(
        "Transaccion",
        back_populates="empresa",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<Empresa(id={self.id}, nombre='{self.nombre}', moneda='{self.moneda_local}')>"