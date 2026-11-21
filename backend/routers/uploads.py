"""
Router de uploads: recibe archivos Excel/CSV, los normaliza con services.ingesta
e inserta las transacciones en la base de datos.
"""
import os
import shutil
from datetime import datetime

from fastapi import APIRouter, Depends, File, UploadFile, Form, HTTPException
from sqlalchemy.orm import Session

from database.connection import get_db
from models import Empresa, Transaccion
from services.ingesta import procesar_archivo, ErrorIngesta

router = APIRouter(prefix="/api/uploads", tags=["Uploads"])

# Carpeta donde se guardan los archivos subidos
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Extensiones permitidas
EXTENSIONES_PERMITIDAS = {".csv", ".xlsx", ".xls"}


@router.post("/excel", summary="Subir Excel/CSV y cargar transacciones")
async def subir_archivo(
    archivo: UploadFile = File(..., description="Archivo CSV, XLSX o XLS"),
    empresa_id: int = Form(..., description="ID de la empresa a la que pertenece el archivo"),
    moneda_default: str = Form("GTQ", description="Moneda por defecto si el archivo no la trae"),
    db: Session = Depends(get_db),
):
    # 1. Validar empresa
    emp = db.query(Empresa).filter(Empresa.id == empresa_id).first()
    if not emp:
        raise HTTPException(status_code=400, detail=f"Empresa con id={empresa_id} no existe")

    # 2. Validar extensión
    nombre_original = archivo.filename or "archivo_sin_nombre"
    ext = os.path.splitext(nombre_original)[1].lower()
    if ext not in EXTENSIONES_PERMITIDAS:
        raise HTTPException(
            status_code=400,
            detail=f"Extensión {ext} no permitida. Usa: {sorted(EXTENSIONES_PERMITIDAS)}",
        )

    # 3. Guardar el archivo en uploads/
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre_seguro = f"{empresa_id}_{timestamp}_{nombre_original}"
    ruta_destino = os.path.join(UPLOAD_DIR, nombre_seguro)

    try:
        with open(ruta_destino, "wb") as buffer:
            shutil.copyfileobj(archivo.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"No se pudo guardar el archivo: {e}")
    finally:
        archivo.file.close()

    # 4. Procesar con el servicio de ingesta
    try:
        resultado = procesar_archivo(
            ruta_destino,
            empresa_id=empresa_id,
            moneda_default=moneda_default,
        )
    except ErrorIngesta as e:
        raise HTTPException(status_code=422, detail=f"Error de ingesta: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {e}")

    df = resultado["dataframe"]

    if df.empty:
        raise HTTPException(
            status_code=422,
            detail="El archivo no contiene filas válidas para insertar.",
        )

    # 5. Insertar transacciones en la BD
    insertadas = 0
    errores_insercion = []
    for _, fila in df.iterrows():
        try:
            tx = Transaccion(
                empresa_id=int(fila["empresa_id"]),
                sucursal_id=None,
                fecha=fila["fecha"],
                cuenta=str(fila["cuenta"])[:20],
                descripcion=(str(fila["descripcion"])[:255] if fila["descripcion"] else None),
                monto=float(fila["monto"]),
                moneda=str(fila["moneda"])[:3],
                monto_base=None,
                banco=(str(fila["banco"])[:80] if fila["banco"] else None),
                categoria=(str(fila["categoria"])[:80] if fila["categoria"] else None),
                es_intercompany=str(fila["es_intercompany"])[:1],
                empresa_contraparte_id=None,
                archivo_origen=str(fila["archivo_origen"])[:255],
                fila_origen=int(fila["fila_origen"]) if fila["fila_origen"] else None,
            )
            db.add(tx)
            insertadas += 1
        except Exception as e:
            errores_insercion.append({"fila": int(fila["fila_origen"]), "error": str(e)})

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al guardar en BD: {e}")

    return {
        "status": "success",
        "archivo": nombre_original,
        "ruta_guardada": ruta_destino,
        "empresa_id": empresa_id,
        "filas_leidas": resultado["filas_leidas"],
        "filas_validas": resultado["filas_validas"],
        "filas_descartadas": resultado["filas_descartadas"],
        "transacciones_insertadas": insertadas,
        "errores_insercion": errores_insercion,
        "columnas_detectadas": resultado["columnas_detectadas"],
    }