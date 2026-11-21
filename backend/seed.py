"""
Seed de datos de prueba: 6 empresas, 3+ monedas, transacciones de balance
y errores sembrados a propósito para el demo del jurado.
"""
import random
from datetime import date, timedelta

from database.connection import SessionLocal, engine, Base
from models import Empresa, Sucursal, Transaccion


# ==================== DATOS BASE ====================

EMPRESAS = [
    {"nombre": "Grupo AG Guatemala", "pais": "Guatemala", "moneda_local": "GTQ"},
    {"nombre": "AG Costa Rica", "pais": "Costa Rica", "moneda_local": "CRC"},
    {"nombre": "AG Mexico", "pais": "Mexico", "moneda_local": "MXN"},
    {"nombre": "AG Honduras", "pais": "Honduras", "moneda_local": "HNL"},
    {"nombre": "AG El Salvador", "pais": "El Salvador", "moneda_local": "USD"},
    {"nombre": "AG Panama", "pais": "Panama", "moneda_local": "USD"},
]

SUCURSALES = [
    {"empresa_idx": 0, "nombre": "Sucursal Central GT", "ciudad": "Guatemala"},
    {"empresa_idx": 0, "nombre": "Sucursal Quetzaltenango", "ciudad": "Quetzaltenango"},
    {"empresa_idx": 1, "nombre": "Sucursal San Jose", "ciudad": "San Jose"},
    {"empresa_idx": 2, "nombre": "Sucursal CDMX", "ciudad": "Ciudad de Mexico"},
    {"empresa_idx": 3, "nombre": "Sucursal Tegucigalpa", "ciudad": "Tegucigalpa"},
    {"empresa_idx": 4, "nombre": "Sucursal San Salvador", "ciudad": "San Salvador"},
    {"empresa_idx": 5, "nombre": "Sucursal Panama City", "ciudad": "Panama"},
]


def _fecha_aleatoria() -> date:
    """Fecha aleatoria en los últimos 90 días."""
    return date.today() - timedelta(days=random.randint(1, 90))


def _crear_transacciones_balance(empresa_id: int, moneda: str) -> list[dict]:
    """
    Crea transacciones de balance (activos y pasivos) para que ROIC/ROCE/EVA
    tengan sentido. Sin esto, el capital invertido sale 1.0.
    """
    txs = []
    # Activos (1xxx)
    txs.append({
        "empresa_id": empresa_id, "sucursal_id": None,
        "fecha": _fecha_aleatoria(), "cuenta": "1100",
        "descripcion": "Caja y bancos", "monto": random.uniform(50000, 200000),
        "moneda": moneda, "banco": "BI", "categoria": "Activo",
        "es_intercompany": "N",
    })
    txs.append({
        "empresa_id": empresa_id, "sucursal_id": None,
        "fecha": _fecha_aleatoria(), "cuenta": "1200",
        "descripcion": "Cuentas por cobrar", "monto": random.uniform(30000, 150000),
        "moneda": moneda, "banco": "BI", "categoria": "Activo",
        "es_intercompany": "N",
    })
    txs.append({
        "empresa_id": empresa_id, "sucursal_id": None,
        "fecha": _fecha_aleatoria(), "cuenta": "1300",
        "descripcion": "Inventario", "monto": random.uniform(20000, 100000),
        "moneda": moneda, "banco": "BI", "categoria": "Activo",
        "es_intercompany": "N",
    })
    # Pasivos (2xxx)
    txs.append({
        "empresa_id": empresa_id, "sucursal_id": None,
        "fecha": _fecha_aleatoria(), "cuenta": "2100",
        "descripcion": "Cuentas por pagar", "monto": random.uniform(15000, 80000),
        "moneda": moneda, "banco": "BI", "categoria": "Pasivo",
        "es_intercompany": "N",
    })
    txs.append({
        "empresa_id": empresa_id, "sucursal_id": None,
        "fecha": _fecha_aleatoria(), "cuenta": "2200",
        "descripcion": "Deuda corto plazo", "monto": random.uniform(10000, 60000),
        "moneda": moneda, "banco": "BI", "categoria": "Pasivo",
        "es_intercompany": "N",
    })
    return txs


def _crear_transacciones_operativas(empresa_id: int, moneda: str, sucursal_id: int | None = None) -> list[dict]:
    """Crea transacciones de ingresos y gastos."""
    txs = []
    # Ingresos (4xxx)
    for _ in range(3):
        txs.append({
            "empresa_id": empresa_id, "sucursal_id": sucursal_id,
            "fecha": _fecha_aleatoria(), "cuenta": "4100",
            "descripcion": "Venta de servicios", "monto": random.uniform(5000, 50000),
            "moneda": moneda, "banco": "BI", "categoria": "Ventas",
            "es_intercompany": "N",
        })
    # Gastos (5xxx) — negativos para que NOPAT = ingresos - gastos funcione
    for _ in range(2):
        txs.append({
            "empresa_id": empresa_id, "sucursal_id": sucursal_id,
            "fecha": _fecha_aleatoria(), "cuenta": "5100",
            "descripcion": "Costo de ventas", "monto": -random.uniform(2000, 20000),
            "moneda": moneda, "banco": "BI", "categoria": "Costos",
            "es_intercompany": "N",
        })
    return txs


def _crear_transacciones_intercompany(empresas: list[Empresa]) -> list[dict]:
    """Crea pares intercompany (venta interna + espejo)."""
    txs = []
    pares = [
        (0, 1, 25000.0),  # GT → CR
        (2, 0, 18000.0),  # MX → GT
        (3, 4, 12000.0),  # HN → SV
    ]
    for orig_idx, dest_idx, monto in pares:
        orig = empresas[orig_idx]
        dest = empresas[dest_idx]
        # Venta interna (empresa origen → destino)
        txs.append({
            "empresa_id": orig.id, "sucursal_id": None,
            "fecha": _fecha_aleatoria(), "cuenta": "4100",
            "descripcion": f"Venta intercompany a {dest.nombre}",
            "monto": monto, "moneda": orig.moneda_local,
            "banco": "BI", "categoria": "Ventas",
            "es_intercompany": "S", "empresa_contraparte_id": dest.id,
        })
        # Espejo (empresa destino registra la compra)
        txs.append({
            "empresa_id": dest.id, "sucursal_id": None,
            "fecha": _fecha_aleatoria(), "cuenta": "5100",
            "descripcion": f"Compra intercompany de {orig.nombre}",
            "monto": -monto, "moneda": dest.moneda_local,
            "banco": "BI", "categoria": "Compras",
            "es_intercompany": "S", "empresa_contraparte_id": orig.id,
        })
    return txs


def _crear_errores_sembrados(empresas: list[Empresa]) -> list[dict]:
    """Errores a propósito para que la aduana los detecte."""
    txs = []
    emp0 = empresas[0]
    emp1 = empresas[1]

    # 1. Duplicado exacto
    dup = {
        "empresa_id": emp0.id, "sucursal_id": None,
        "fecha": date(2026, 11, 15), "cuenta": "4100",
        "descripcion": "Venta duplicada error", "monto": 9999.99,
        "moneda": "GTQ", "banco": "BI", "categoria": "Ventas",
        "es_intercompany": "N",
    }
    txs.append(dup)
    txs.append(dup.copy())

    # 2. Moneda inválida
    txs.append({
        "empresa_id": emp0.id, "sucursal_id": None,
        "fecha": date(2026, 11, 16), "cuenta": "4100",
        "descripcion": "Venta con moneda rara", "monto": 5000.0,
        "moneda": "XYZ", "banco": "BI", "categoria": "Ventas",
        "es_intercompany": "N",
    })

    # 3. Signo invertido (ingreso negativo)
    txs.append({
        "empresa_id": emp1.id, "sucursal_id": None,
        "fecha": date(2026, 11, 17), "cuenta": "4100",
        "descripcion": "Ingreso con signo mal", "monto": -3000.0,
        "moneda": emp1.moneda_local, "banco": "BI", "categoria": "Ventas",
        "es_intercompany": "N",
    })

    # 4. Intercompany sin contraparte
    txs.append({
        "empresa_id": emp0.id, "sucursal_id": None,
        "fecha": date(2026, 11, 18), "cuenta": "4100",
        "descripcion": "Venta intercompany huérfana", "monto": 7000.0,
        "moneda": "GTQ", "banco": "BI", "categoria": "Ventas",
        "es_intercompany": "S", "empresa_contraparte_id": None,
    })

    # 5. Cuenta huérfana
    txs.append({
        "empresa_id": emp0.id, "sucursal_id": None,
        "fecha": date(2026, 11, 19), "cuenta": "9999",
        "descripcion": "Cuenta inexistente", "monto": 1500.0,
        "moneda": "GTQ", "banco": "BI", "categoria": "Otros",
        "es_intercompany": "N",
    })

    return txs


def seed():
    """Ejecuta el seed completo."""
    print("Creando tablas...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Limpiar datos previos
        print("Limpiando transacciones previas...")
        db.query(Transaccion).delete()
        db.query(Sucursal).delete()
        db.query(Empresa).delete()
        db.commit()

        # 1. Empresas
        print("Creando 6 empresas...")
        empresas = []
        for data in EMPRESAS:
            emp = Empresa(**data)
            db.add(emp)
            empresas.append(emp)
        db.commit()
        for emp in empresas:
            db.refresh(emp)
        print(f"  → {len(empresas)} empresas creadas")

        # 2. Sucursales
        print("Creando sucursales...")
        sucursales = []
        for data in SUCURSALES:
            idx = data.pop("empresa_idx")
            suc = Sucursal(empresa_id=empresas[idx].id, **data)
            db.add(suc)
            sucursales.append(suc)
        db.commit()
        for suc in sucursales:
            db.refresh(suc)
        print(f"  → {len(sucursales)} sucursales creadas")

        # 3. Transacciones de balance + operativas por empresa
        print("Creando transacciones de balance y operativas...")
        total_tx = 0
        for i, emp in enumerate(empresas):
            txs_balance = _crear_transacciones_balance(emp.id, emp.moneda_local)
            txs_operativas = _crear_transacciones_operativas(emp.id, emp.moneda_local)
            for data in txs_balance + txs_operativas:
                db.add(Transaccion(**data))
                total_tx += 1
        db.commit()
        print(f"  → {total_tx} transacciones normales creadas")

        # 4. Intercompany
        print("Creando transacciones intercompany...")
        txs_inter = _crear_transacciones_intercompany(empresas)
        for data in txs_inter:
            db.add(Transaccion(**data))
        db.commit()
        print(f"  → {len(txs_inter)} transacciones intercompany creadas")

        # 5. Errores sembrados
        print("Sembrando errores a propósito...")
        txs_errores = _crear_errores_sembrados(empresas)
        for data in txs_errores:
            db.add(Transaccion(**data))
        db.commit()
        print(f"  → {len(txs_errores)} transacciones con errores sembrados")

        # Resumen
        total = db.query(Transaccion).count()
        print("\n=== SEED COMPLETADO ===")
        print(f"Empresas: {db.query(Empresa).count()}")
        print(f"Sucursales: {db.query(Sucursal).count()}")
        print(f"Transacciones: {total}")
        print(f"  - Intercompany: {db.query(Transaccion).filter(Transaccion.es_intercompany == 'S').count()}")
        print(f"  - Con errores: {len(txs_errores)}")

    except Exception as e:
        db.rollback()
        print(f"ERROR en seed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()