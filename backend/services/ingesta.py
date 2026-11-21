"""
Servicio de ingesta: lee archivos Excel/CSV heterogéneos y los normaliza
a un esquema maestro común para consolidación.
"""
import os
import re
from datetime import datetime
from typing import Optional

import pandas as pd


# Mapa flexible: cada campo estándar acepta varios nombres posibles en los archivos
MAPEO_COLUMNAS = {
    "fecha": ["fecha", "date", "dia", "fecha_operacion", "fecha operacion"],
    "cuenta": ["cuenta", "cuenta_contable", "codigo_cuenta", "cod cuenta", "account", "cuenta contable"],
    "descripcion": ["descripcion", "descripción", "detalle", "concepto", "item", "glosa"],
    "monto": ["monto", "valor", "importe", "total", "amount", "debito", "credito"],
    "moneda": ["moneda", "currency", "divisa", "moneda_original"],
    "sucursal": ["sucursal", "branch", "agencia", "tienda", "local"],
    "banco": ["banco", "bank", "entidad", "entidad_bancaria"],
    "categoria": ["categoria", "categoría", "category", "tipo", "clasificacion"],
    "es_intercompany": ["intercompany", "es_intercompany", "inter compañía", "intra_grupo"],
    "empresa_contraparte": ["contraparte", "empresa_contraparte", "empresa_relacionada"],
}


class ErrorIngesta(Exception):
    """Error controlado durante la ingesta de un archivo."""
    pass


def _normalizar_nombre_columna(col: str) -> str:
    """Convierte un nombre de columna a minúsculas, sin tildes, sin espacios extra."""
    col = str(col).strip().lower()
    col = (
        col.replace("á", "a").replace("é", "e").replace("í", "i")
        .replace("ó", "o").replace("ú", "u").replace("ñ", "n")
    )
    col = re.sub(r"\s+", " ", col)
    return col


def _detectar_columnas(df: pd.DataFrame) -> dict:
    """
    Devuelve un dict {campo_estandar: nombre_real_en_df} para los campos
    que se encontraron en el DataFrame.
    """
    columnas_normalizadas = {_normalizar_nombre_columna(c): c for c in df.columns}
    encontradas = {}

    for campo_estandar, alias_posibles in MAPEO_COLUMNAS.items():
        for alias in alias_posibles:
            alias_norm = _normalizar_nombre_columna(alias)
            if alias_norm in columnas_normalizadas:
                encontradas[campo_estandar] = columnas_normalizadas[alias_norm]
                break

    return encontradas


def _limpiar_monto(valor) -> Optional[float]:
    """Convierte 'Q 1,500.50', '$1.500,50', '1500.50' a float. Devuelve None si no puede."""
    if pd.isna(valor) or valor == "":
        return None
    if isinstance(valor, (int, float)):
        return float(valor)
    texto = str(valor).strip()
    # Eliminar símbolos de moneda, espacios y letras
    texto = re.sub(r"[^\d,.\-]", "", texto)
    if texto == "":
        return None
    # Heurística: si hay coma y punto, el que está al final es el decimal
    if "," in texto and "." in texto:
        if texto.rfind(",") > texto.rfind("."):
            texto = texto.replace(".", "").replace(",", ".")
        else:
            texto = texto.replace(",", "")
    elif "," in texto and "." not in texto:
        # 1500,50 → 1500.50
        if len(texto.split(",")[-1]) == 2:
            texto = texto.replace(",", ".")
        else:
            texto = texto.replace(",", "")
    try:
        return float(texto)
    except ValueError:
        return None


def _limpiar_fecha(valor) -> Optional[datetime.date]:
    """Intenta parsear fechas en varios formatos comunes."""
    if pd.isna(valor) or valor == "":
        return None
    if isinstance(valor, datetime):
        return valor.date()
    texto = str(valor).strip()
    formatos = ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%Y/%m/%d", "%d.%m.%Y"]
    for fmt in formatos:
        try:
            return datetime.strptime(texto, fmt).date()
        except ValueError:
            continue
    # Último intento: pandas
    try:
        return pd.to_datetime(texto, dayfirst=True).date()
    except Exception:
        return None


def leer_archivo(file_path: str) -> pd.DataFrame:
    """Lee CSV o Excel según la extensión."""
    if not os.path.exists(file_path):
        raise ErrorIngesta(f"Archivo no encontrado: {file_path}")

    ext = os.path.splitext(file_path)[1].lower()
    try:
        if ext == ".csv":
            # Detectar separador automáticamente (coma o punto y coma)
            df = pd.read_csv(file_path, sep=None, engine="python", encoding="utf-8-sig")
        elif ext in (".xlsx", ".xls"):
            df = pd.read_excel(file_path)
        else:
            raise ErrorIngesta(f"Extensión no soportada: {ext}. Usa CSV, XLSX o XLS.")
    except ErrorIngesta:
        raise
    except Exception as e:
        raise ErrorIngesta(f"No se pudo leer el archivo: {e}")

    if df.empty:
        raise ErrorIngesta("El archivo está vacío.")

    return df


def normalizar_dataframe(
    df: pd.DataFrame,
    empresa_id: int,
    archivo_origen: str,
    moneda_default: str = "GTQ",
) -> pd.DataFrame:
    """
    Toma un DataFrame crudo de cualquier sucursal y devuelve un DataFrame
    con el esquema maestro listo para insertar en la tabla `transacciones`.
    """
    columnas = _detectar_columnas(df)

    faltantes = [c for c in ["fecha", "cuenta", "monto"] if c not in columnas]
    if faltantes:
        raise ErrorIngesta(
            f"Faltan columnas obligatorias: {faltantes}. "
            f"Columnas detectadas: {list(df.columns)}"
        )

    resultado = pd.DataFrame(index=df.index)
    resultado["empresa_id"] = empresa_id
    resultado["fecha"] = df[columnas["fecha"]].apply(_limpiar_fecha)
    resultado["cuenta"] = df[columnas["cuenta"]].astype(str).str.strip()
    resultado["descripcion"] = (
        df[columnas["descripcion"]].astype(str).str.strip()
        if "descripcion" in columnas else None
    )
    resultado["monto"] = df[columnas["monto"]].apply(_limpiar_monto)
    resultado["moneda"] = (
        df[columnas["moneda"]].astype(str).str.strip().str.upper()
        if "moneda" in columnas else moneda_default
    )
    resultado["banco"] = (
        df[columnas["banco"]].astype(str).str.strip()
        if "banco" in columnas else None
    )
    resultado["categoria"] = (
        df[columnas["categoria"]].astype(str).str.strip()
        if "categoria" in columnas else None
    )
    resultado["es_intercompany"] = (
        df[columnas["es_intercompany"]]
        .astype(str).str.strip().str.upper()
        .replace({"TRUE": "S", "FALSE": "N", "1": "S", "0": "N"})
        .where(lambda s: s.isin(["S", "N"]), "N")
        if "es_intercompany" in columnas else "N"
    )
    resultado["empresa_contraparte_id"] = None
    resultado["archivo_origen"] = os.path.basename(archivo_origen)
    resultado["fila_origen"] = range(2, len(resultado) + 2)  # fila 1 = cabecera

    # Descartar filas sin fecha o sin monto (no son transacciones válidas)
    resultado = resultado.dropna(subset=["fecha", "monto"]).reset_index(drop=True)

    # Asegurar tipos correctos para la inserción en BD
    resultado["empresa_id"] = resultado["empresa_id"].astype(int)
    resultado["monto"] = resultado["monto"].astype(float)
    resultado["fila_origen"] = resultado["fila_origen"].astype(int)

    return resultado


def procesar_archivo(
    file_path: str,
    empresa_id: int,
    moneda_default: str = "GTQ",
) -> dict:
    """
    Pipeline completo: leer → normalizar → devolver dict con resultados.
    No toca la BD; eso lo hace el router.
    """
    df_crudo = leer_archivo(file_path)
    df_norm = normalizar_dataframe(
        df_crudo,
        empresa_id=empresa_id,
        archivo_origen=file_path,
        moneda_default=moneda_default,
    )

    return {
        "archivo": os.path.basename(file_path),
        "empresa_id": empresa_id,
        "filas_leidas": len(df_crudo),
        "filas_validas": len(df_norm),
        "filas_descartadas": len(df_crudo) - len(df_norm),
        "columnas_detectadas": list(_detectar_columnas(df_crudo).keys()),
        "dataframe": df_norm,
    }