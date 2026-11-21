import math
from typing import Optional

from fastapi import APIRouter, HTTPException

from database.connection import SessionLocal
from models import Transaccion
from services.consolidacion import consolidar_grupo, TASAS_CAMBIO

router = APIRouter(prefix="/api/trazabilidad", tags=["Trazabilidad"])

PREFIJOS = {"ingresos": "4", "gastos": "5", "activos": "1", "pasivos": "2"}


def _limpiar(d: dict) -> dict:
    """pandas convierte None en NaN y eso rompe el JSON."""
    return {
        k: (None if isinstance(v, float) and math.isnan(v) else v)
        for k, v in d.items()
    }


def _filas():
    db = SessionLocal()
    try:
        return [
            {c.name: getattr(t, c.name) for c in t.__table__.columns}
            for t in db.query(Transaccion).all()
        ]
    finally:
        db.close()


@router.get("/{componente}")
def trazar(componente: str, empresa_id: Optional[int] = None):
    """
    Drill-down: de qué transacciones sale cada cifra.
    componente: ingresos | gastos | activos | pasivos
    """
    if componente not in PREFIJOS:
        raise HTTPException(400, f"Componente inválido. Usa: {list(PREFIJOS)}")

    r = consolidar_grupo(_filas())
    pref = PREFIJOS[componente]

    detalle = []
    for t in r["transacciones_limpias"]:
        if not str(t.get("cuenta", "")).startswith(pref):
            continue
        if empresa_id and t.get("empresa_id") != empresa_id:
            continue
        t = _limpiar(t)
        moneda = str(t.get("moneda", "")).upper()
        detalle.append({
            "id": t.get("id"),
            "empresa_id": t.get("empresa_id"),
            "fecha": str(t.get("fecha")),
            "cuenta": t.get("cuenta"),
            "descripcion": t.get("descripcion"),
            "monto_original": t.get("monto"),
            "moneda": moneda,
            "tasa_aplicada": TASAS_CAMBIO.get(moneda),
            "monto_gtq": t.get("monto_base"),
            "es_intercompany": t.get("es_intercompany"),
        })

    return {
        "componente": componente,
        "empresa_id": empresa_id,
        "total_registros": len(detalle),
        "total_gtq": round(sum(abs(d["monto_gtq"] or 0) for d in detalle), 2),
        "registros": detalle,
        "intercompany_eliminadas": r["intercompany"]["eliminadas"],
    }