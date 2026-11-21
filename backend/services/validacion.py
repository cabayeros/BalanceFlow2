"""
Servicio de validación: la 'aduana financiera'.
Detecta errores sembrados antes de que toquen el consolidado.
"""
from collections import defaultdict
from typing import Any

import pandas as pd


# Catálogo de cuentas contables válidas (puedes ampliarlo)
CUENTAS_VALIDAS = {
    "1100", "1200", "1300",  # Activos
    "2100", "2200", "2300",  # Pasivos
    "3100", "3200",          # Patrimonio
    "4100", "4200",          # Ingresos
    "5100", "5200", "5300",  # Costos y gastos
}

MONEDAS_VALIDAS = {"GTQ", "USD", "EUR", "MXN", "CRC", "HNL", "NIO", "PAB"}

# Cuentas que deben ser positivas (ingresos) y negativas (gastos)
PREFIJOS_INGRESO = ("4",)
PREFIJOS_GASTO = ("5",)


class ErrorValidacion(Exception):
    """Error controlado en la validación."""
    pass


def _es_gasto(cuenta: str) -> bool:
    return str(cuenta).startswith(PREFIJOS_GASTO)


def _es_ingreso(cuenta: str) -> bool:
    return str(cuenta).startswith(PREFIJOS_INGRESO)


def validar_transacciones(transacciones: list[dict]) -> dict:
    """
    Recibe una lista de dicts (cada uno con los campos de Transaccion)
    y devuelve un reporte con:
      - estado: "LIMPIO" o "CON_ERRORES"
      - total_registros
      - errores: lista de dicts con tipo, severidad, mensaje, fila, datos
      - alertas: lista de advertencias no bloqueantes
    """
    errores: list[dict] = []
    alertas: list[dict] = []

    if not transacciones:
        return {
            "estado": "LIMPIO",
            "total_registros": 0,
            "errores": [],
            "alertas": [],
        }

    # --- 1. Validar monedas ---
    for i, tx in enumerate(transacciones):
        moneda = str(tx.get("moneda", "")).upper().strip()
        if moneda not in MONEDAS_VALIDAS:
            errores.append({
                "tipo": "MONEDA_INVALIDA",
                "severidad": "CRITICO",
                "fila": tx.get("fila_origen", i + 2),
                "mensaje": f"Moneda '{moneda}' no está en el catálogo válido {sorted(MONEDAS_VALIDAS)}",
                "datos": {"monto": tx.get("monto"), "cuenta": tx.get("cuenta")},
            })

    # --- 2. Validar cuentas huérfanas ---
    for i, tx in enumerate(transacciones):
        cuenta = str(tx.get("cuenta", "")).strip()
        if cuenta not in CUENTAS_VALIDAS:
            errores.append({
                "tipo": "CUENTA_HUERFANA",
                "severidad": "ADVERTENCIA",
                "fila": tx.get("fila_origen", i + 2),
                "mensaje": f"Cuenta '{cuenta}' no existe en el catálogo. Revísala o agrégala.",
                "datos": {"monto": tx.get("monto")},
            })

    # --- 3. Validar signos invertidos ---
    for i, tx in enumerate(transacciones):
        cuenta = str(tx.get("cuenta", "")).strip()
        monto = tx.get("monto", 0)
        if monto is None:
            continue
        try:
            monto = float(monto)
        except (TypeError, ValueError):
            continue

        if _es_gasto(cuenta) and monto > 0:
            # Un gasto positivo no necesariamente es error (depende de la convención),
            # pero lo marcamos como advertencia para revisión
            alertas.append({
                "tipo": "GASTO_POSITIVO",
                "severidad": "ADVERTENCIA",
                "fila": tx.get("fila_origen", i + 2),
                "mensaje": f"Gasto (cuenta {cuenta}) con signo positivo ({monto}). Verifica convención.",
                "datos": {"monto": monto},
            })
        if _es_ingreso(cuenta) and monto < 0:
            errores.append({
                "tipo": "INGRESO_NEGATIVO",
                "severidad": "CRITICO",
                "fila": tx.get("fila_origen", i + 2),
                "mensaje": f"Ingreso (cuenta {cuenta}) con signo negativo ({monto}). Probable signo invertido.",
                "datos": {"monto": monto},
            })

    # --- 4. Detectar duplicados exactos ---
    # Clave: (empresa_id, fecha, cuenta, monto, moneda, descripcion)
    vistos: dict[tuple, list[int]] = defaultdict(list)
    for i, tx in enumerate(transacciones):
        clave = (
            tx.get("empresa_id"),
            str(tx.get("fecha")),
            str(tx.get("cuenta")),
            round(float(tx.get("monto", 0) or 0), 2),
            str(tx.get("moneda")),
            str(tx.get("descripcion") or "").strip().lower(),
        )
        vistos[clave].append(tx.get("fila_origen", i + 2))

    for clave, filas in vistos.items():
        if len(filas) > 1:
            errores.append({
                "tipo": "DUPLICADO",
                "severidad": "CRITICO",
                "fila": filas[0],
                "mensaje": f"Transacción duplicada en filas {filas}: empresa={clave[0]}, fecha={clave[1]}, cuenta={clave[2]}, monto={clave[3]}",
                "datos": {"filas_duplicadas": filas, "clave": list(clave)},
            })

    # --- 5. Descuadre intercompany ---
    # Buscar pares: una empresa marca es_intercompany="S" y tiene empresa_contraparte_id
    # La contraparte debe tener una transacción espejo (mismo monto, cuenta opuesta)
    intercompany = [tx for tx in transacciones if str(tx.get("es_intercompany", "N")).upper() == "S"]

    for tx in intercompany:
        contraparte_id = tx.get("empresa_contraparte_id")
        if contraparte_id is None:
            errores.append({
                "tipo": "INTERCOMPANY_SIN_CONTRAPARTE",
                "severidad": "CRITICO",
                "fila": tx.get("fila_origen", 0),
                "mensaje": "Transacción marcada intercompany pero sin empresa_contraparte_id.",
                "datos": {"empresa_id": tx.get("empresa_id"), "monto": tx.get("monto")},
            })
            continue

        # Buscar el espejo
        monto = round(float(tx.get("monto", 0) or 0), 2)
        espejo = [
            t for t in transacciones
            if t.get("empresa_id") == contraparte_id
            and str(t.get("es_intercompany", "N")).upper() == "S"
            and round(float(t.get("monto", 0) or 0), 2) == monto
        ]
        if not espejo:
            errores.append({
                "tipo": "INTERCOMPANY_ASIMETRICO",
                "severidad": "CRITICO",
                "fila": tx.get("fila_origen", 0),
                "mensaje": f"Venta intercompany de empresa {tx.get('empresa_id')} a {contraparte_id} por {monto} sin contrapartida espejo.",
                "datos": {"monto": monto, "contraparte_id": contraparte_id},
            })

    estado = "CON_ERRORES" if errores else "LIMPIO"

    return {
        "estado": estado,
        "total_registros": len(transacciones),
        "errores": errores,
        "alertas": alertas,
        "resumen": {
            "criticos": sum(1 for e in errores if e["severidad"] == "CRITICO"),
            "advertencias": sum(1 for e in errores if e["severidad"] == "ADVERTENCIA"),
            "total_alertas": len(alertas),
        },
    }


def validar_dataframe(df: pd.DataFrame) -> dict:
    """Wrapper: convierte un DataFrame a lista de dicts y valida."""
    return validar_transacciones(df.to_dict(orient="records"))