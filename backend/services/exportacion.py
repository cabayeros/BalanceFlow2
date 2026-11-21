"""Generación de libros Excel para los reportes de BalanceFlow."""
from io import BytesIO

import pandas as pd


def generar_excel_consolidado(reporte: dict) -> bytes:
    """Construye un libro con indicadores, empresas y eliminaciones internas."""
    consolidado = reporte.get("consolidado", {})
    empresas = reporte.get("por_empresa", [])
    intercompany = reporte.get("intercompany", {})
    movimientos = reporte.get("transacciones_limpias", [])

    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        pd.DataFrame([consolidado]).to_excel(writer, sheet_name="Consolidado", index=False)
        pd.DataFrame(empresas).to_excel(writer, sheet_name="Por empresa", index=False)
        pd.DataFrame(intercompany.get("eliminadas", [])).to_excel(
            writer, sheet_name="Eliminaciones", index=False
        )
        pd.DataFrame(intercompany.get("descuadres", [])).to_excel(
            writer, sheet_name="Descuadres", index=False
        )
        pd.DataFrame(movimientos).to_excel(writer, sheet_name="Movimientos", index=False)

    return buffer.getvalue()
