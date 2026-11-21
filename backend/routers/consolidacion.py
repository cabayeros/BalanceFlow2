"""
Router de consolidación: endpoints para consolidar el grupo,
ver indicadores financieros y explicar desviaciones.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database.connection import get_db
from models import Transaccion
from services.consolidacion import consolidar_grupo, ErrorConsolidacion

router = APIRouter(prefix="/api/consolidacion", tags=["Consolidación"])


@router.get("/resumen", summary="Consolidado del grupo con indicadores")
def resumen_consolidado(db: Session = Depends(get_db)):
    """
    Trae todas las transacciones de la BD, las consolida (convierte monedas,
    elimina intercompany) y devuelve el consolidado + indicadores por empresa.
    """
    transacciones = db.query(Transaccion).all()
    if not transacciones:
        raise HTTPException(status_code=404, detail="No hay transacciones para consolidar.")

    datos = [
        {
            "id": t.id,
            "empresa_id": t.empresa_id,
            "sucursal_id": t.sucursal_id,
            "fecha": str(t.fecha),
            "cuenta": t.cuenta,
            "descripcion": t.descripcion,
            "monto": t.monto,
            "moneda": t.moneda,
            "monto_base": t.monto_base,
            "banco": t.banco,
            "categoria": t.categoria,
            "es_intercompany": t.es_intercompany,
            "empresa_contraparte_id": t.empresa_contraparte_id,
            "archivo_origen": t.archivo_origen,
            "fila_origen": t.fila_origen,
        }
        for t in transacciones
    ]

    try:
        resultado = consolidar_grupo(datos)
    except ErrorConsolidacion as e:
        raise HTTPException(status_code=422, detail=str(e))

    return {
        "consolidado": resultado["consolidado"],
        "por_empresa": resultado["por_empresa"],
        "intercompany": resultado["intercompany"],
        "total_transacciones_originales": len(datos),
        "total_transacciones_limpias": len(resultado["transacciones_limpias"]),
    }


@router.get("/por-empresa/{empresa_id}", summary="Indicadores de una empresa")
def indicadores_empresa(empresa_id: int, db: Session = Depends(get_db)):
    transacciones = db.query(Transaccion).filter(Transaccion.empresa_id == empresa_id).all()
    if not transacciones:
        raise HTTPException(status_code=404, detail=f"No hay transacciones para empresa {empresa_id}")

    datos = [
        {
            "id": t.id, "empresa_id": t.empresa_id, "fecha": str(t.fecha),
            "cuenta": t.cuenta, "descripcion": t.descripcion,
            "monto": t.monto, "moneda": t.moneda, "monto_base": t.monto_base,
            "es_intercompany": t.es_intercompany,
            "empresa_contraparte_id": t.empresa_contraparte_id,
        }
        for t in transacciones
    ]

    try:
        resultado = consolidar_grupo(datos)
    except ErrorConsolidacion as e:
        raise HTTPException(status_code=422, detail=str(e))

    return {
        "empresa_id": empresa_id,
        "consolidado": resultado["consolidado"],
        "detalle": resultado["por_empresa"],
    }


@router.get("/intercompany", summary="Detalle de eliminaciones intercompany")
def detalle_intercompany(db: Session = Depends(get_db)):
    transacciones = db.query(Transaccion).all()
    if not transacciones:
        raise HTTPException(status_code=404, detail="No hay transacciones.")

    datos = [
        {
            "id": t.id, "empresa_id": t.empresa_id, "fecha": str(t.fecha),
            "cuenta": t.cuenta, "monto": t.monto, "moneda": t.moneda,
            "monto_base": t.monto_base, "es_intercompany": t.es_intercompany,
            "empresa_contraparte_id": t.empresa_contraparte_id,
            "fila_origen": t.fila_origen,
        }
        for t in transacciones
    ]

    resultado = consolidar_grupo(datos)
    return resultado["intercompany"]