from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Date, func
from sqlalchemy.orm import relationship
from database.connection import Base


class Transaccion(Base):
    __tablename__ = "transacciones"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False, index=True)
    sucursal_id = Column(Integer, ForeignKey("sucursales.id"), nullable=True, index=True)

    # Datos financieros
    fecha = Column(Date, nullable=False)
    cuenta = Column(String(20), nullable=False, index=True)
    descripcion = Column(String(255), nullable=True)
    monto = Column(Float, nullable=False)
    moneda = Column(String(3), nullable=False)
    monto_base = Column(Float, nullable=True)  # convertido a moneda base del grupo

    # Clasificación / trazabilidad
    banco = Column(String(80), nullable=True)
    categoria = Column(String(80), nullable=True)
    es_intercompany = Column(String(1), default="N", nullable=False)  # "S" o "N"
    empresa_contraparte_id = Column(Integer, nullable=True)
    archivo_origen = Column(String(255), nullable=True)
    fila_origen = Column(Integer, nullable=True)
    creada_en = Column(DateTime, server_default=func.now(), nullable=False)

    # Relaciones
    empresa = relationship("Empresa", back_populates="transacciones")

    def __repr__(self):
        return (
            f"<Transaccion(id={self.id}, fecha={self.fecha}, "
            f"monto={self.monto} {self.moneda}, empresa_id={self.empresa_id})>"
        )