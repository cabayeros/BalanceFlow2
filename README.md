# BalanceFlow

**Consolidación financiera multiempresa que se adapta a cómo trabaja cada empresa.**

BalanceFlow es un backend (API REST) que toma la información financiera de varias empresas de un mismo grupo, aunque estén en distintos países, monedas y formatos, y la convierte en un único número confiable para el grupo: sin sumas manuales, sin ventas internas contadas doble y con cada cifra rastreable hasta el registro que la originó.

> Proyecto desarrollado para **Build & Pitch** (track Accounting: consolidación multiempresa), UVG, 21 de noviembre de 2026.

---

## ¿Qué problema resuelve?

Un grupo con varias empresas ya presupuesta bien cada área por separado. Lo que falla es juntar todo:

| Problema | Cómo lo resuelve BalanceFlow |
|---|---|
| Consolidación manual, cada empresa con su formato | Importación y normalización de datos a un esquema único |
| Ventas entre empresas del grupo se cuentan doble | Cruce automático de operaciones intercompany y eliminación de pares |
| Varias monedas sin tasa común | Conversión a moneda base (GTQ) con tabla de tasas centralizada |
| ROIC, ROCE y EVA copiados a mano | Cálculo automático desde los registros |
| Cifras que cambian sin explicación | Endpoint de trazabilidad (drill-down) hasta la transacción original |
| Errores que entran al número del grupo | Datos con errores sembrados para probar la detección de inconsistencias |

**Principio de diseño:** adaptarse a la empresa, no obligar a la empresa a adaptarse al software. BalanceFlow no reemplaza ERP, Excel ni procesos existentes: funciona como una capa de integración y automatización encima de ellos.

---

## Funcionalidades

- **Gestión multiempresa y multisucursal:** CRUD de empresas, sucursales y transacciones.
- **Conversión de monedas** a moneda base del grupo (GTQ). Monedas no reconocidas no rompen la consolidación.
- **Eliminación de intercompany:** empareja venta y compra espejo entre empresas (comparando en moneda base, con tolerancia de 1 GTQ) y reporta los descuadres (sin contraparte, asimétricos).
- **Indicadores financieros por empresa y por grupo:** NOPAT, capital invertido, ROIC, ROCE y EVA.
- **Trazabilidad:** para cada componente (ingresos, gastos, activos, pasivos) se obtiene el detalle de transacciones, la tasa aplicada y el monto convertido.
- **Exportación** del consolidado limpio a CSV.
- **Carga de archivos** (Excel/CSV) mediante el router de `uploads`.
- **CORS configurado** para conectarse con un frontend (React, etc.).
- **Documentación interactiva** automática con Swagger en `/docs`.

---

## Stack tecnológico

| Capa | Tecnología |
|---|---|
| API | Python, FastAPI, Uvicorn |
| Validación | Pydantic |
| Persistencia | SQLAlchemy + SQLite (desarrollo); PostgreSQL previsto para producción |
| Procesamiento | Pandas, OpenPyXL |
| Frontend (equipo) | React, TypeScript, Tailwind CSS |

---

## Estructura del proyecto

```
BalanceFlow/
├── backend/
│   ├── main.py                  # App FastAPI, CORS, routers y CRUD base
│   ├── seed.py                  # Datos de prueba (6 empresas, errores sembrados)
│   ├── models.py                # Modelos: Empresa, Sucursal, Transaccion
│   ├── schemas.py               # Esquemas Pydantic
│   ├── core/
│   │   └── config.py            # Configuración (variables de entorno)
│   ├── database/
│   │   └── connection.py        # Engine, sesión y Base de SQLAlchemy
│   ├── routers/
│   │   ├── uploads.py           # Carga de archivos
│   │   ├── consolidacion.py     # Resumen consolidado
│   │   ├── trazabilidad.py      # Drill-down por cifra
│   │   └── exportacion.py       # Exportación CSV
│   ├── services/
│   │   └── consolidacion.py     # Motor: monedas, intercompany, ROIC/ROCE/EVA
│   └── balanceflow.db           # Base SQLite (se genera sola)
└── frontend/                    # Interfaz React (responsabilidad del equipo de UI)
```

---

## Requisitos previos

- **Python 3.12 o superior** (recomendado 3.12 o 3.13 para máxima compatibilidad de librerías).
- **Git**.
- Windows, macOS o Linux. Los ejemplos usan PowerShell (Windows).

> En Windows, durante la instalación de Python marca **"Add python.exe to PATH"**.

---

## Instalación

### 1. Clonar el repositorio

```powershell
git clone https://github.com/DM-182JKDD/BalanceFlow.git
cd BalanceFlow\backend
```

### 2. Crear y activar el entorno virtual

**Windows (PowerShell):**
```powershell
python -m venv venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\venv\Scripts\Activate.ps1
```

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

Sabrás que está activo porque verás `(venv)` al inicio de la línea.

### 3. Instalar dependencias

```powershell
pip install fastapi uvicorn sqlalchemy pandas openpyxl python-multipart pydantic pydantic-settings
```

Si el repositorio incluye `requirements.txt`, puedes usar:

```powershell
pip install -r requirements.txt
```

### 4. Cargar datos de prueba

```powershell
python seed.py
```

Esto crea las tablas y puebla la base con datos ficticios. Resultado esperado:

```
Empresas: 6
Sucursales: 7
Transacciones: 72
```

> Detén el servidor (`Ctrl + C`) antes de ejecutar el seed para evitar bloqueos de SQLite. El seed **borra y recrea** los datos existentes.

---

## Cómo correrlo

```powershell
uvicorn main:app --reload
```

| URL | Para qué |
|---|---|
| http://127.0.0.1:8000 | Estado del servicio |
| http://127.0.0.1:8000/docs | Documentación interactiva (Swagger), ideal para probar |
| http://127.0.0.1:8000/health | Verificación de salud y conexión a la base |

---

## Cómo se usa

### Flujo típico

1. **Registrar o cargar datos** de empresas, sucursales y transacciones (por API o con `seed.py` para la demo).
2. **Consolidar:** `GET /api/consolidacion/resumen` convierte monedas, elimina intercompany y calcula indicadores.
3. **Auditar:** `GET /api/trazabilidad/{componente}` muestra de qué transacciones sale cada cifra.
4. **Exportar:** `GET /api/exportacion/csv` descarga el consolidado limpio.

### Endpoints principales

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/empresas` | Lista de empresas |
| POST | `/api/empresas` | Crear empresa |
| GET/PATCH/DELETE | `/api/empresas/{id}` | Consultar, actualizar, eliminar |
| GET/POST | `/api/sucursales` | Listar (filtro `empresa_id`) / crear |
| GET/POST | `/api/transacciones` | Listar (filtros `empresa_id`, `sucursal_id`) / crear |
| GET | `/api/consolidacion/resumen` | Consolidado del grupo, por empresa e intercompany |
| GET | `/api/trazabilidad/{componente}` | Drill-down. `componente`: `ingresos`, `gastos`, `activos`, `pasivos`. Filtro opcional `empresa_id` |
| GET | `/api/exportacion/csv` | Descarga CSV del consolidado limpio |

### Ejemplos

```powershell
# Consolidado del grupo
curl http://127.0.0.1:8000/api/consolidacion/resumen

# De qué transacciones salen los ingresos de la empresa 1
curl "http://127.0.0.1:8000/api/trazabilidad/ingresos?empresa_id=1"

# Descargar el consolidado
curl -o consolidado.csv http://127.0.0.1:8000/api/exportacion/csv
```

---

## Cómo se calculan los indicadores

Fórmulas simplificadas para el prototipo, por empresa y a nivel grupo, siempre en moneda base (GTQ):

```
NOPAT              = Ingresos (cuentas 4xxx) − Gastos (cuentas 5xxx)
Capital invertido  = Activos (1xxx) − Pasivos (2xxx)
ROIC               = NOPAT / Capital invertido
ROCE               = EBIT / Capital empleado
EVA                = NOPAT − (Capital invertido × WACC)
```

- **WACC:** 10% (valor ficticio de demostración).
- **Tasas de cambio** ficticias, definidas en `services/consolidacion.py` (`TASAS_CAMBIO`): USD 7.85, MXN 0.45, CRC 0.015, HNL 0.32, entre otras.
- **Intercompany:** dos transacciones forman un par si cada una apunta a la otra como contraparte y su monto en GTQ (valor absoluto) difiere en 1 GTQ o menos. Los pares se eliminan; lo que no cuadra se conserva y se reporta como descuadre.

---

## Datos de demostración

El seed genera un grupo ficticio: **6 empresas** (Guatemala, Costa Rica, México, Honduras, El Salvador, Panamá) en varias monedas, con transacciones de balance, operativas e intercompany. Incluye **errores sembrados a propósito**:

1. Transacción duplicada exacta.
2. Moneda inválida (`XYZ`).
3. Ingreso con signo invertido.
4. Intercompany sin contraparte.
5. Cuenta inexistente (`9999`).

No contiene ningún dato real.

---

## Solución de problemas

| Error | Causa y solución |
|---|---|
| `ImportError: cannot import name '...' from 'routers'` | Falta un archivo en `routers/` (`uploads`, `consolidacion`, `trazabilidad` o `exportacion`) |
| `ModuleNotFoundError` | El entorno virtual no está activo o faltan dependencias |
| `database is locked` | El servidor estaba corriendo mientras se ejecutaba `seed.py` |
| `python` abre la Microsoft Store | Python no está en el PATH; reinstálalo marcando "Add python.exe to PATH" |
| Error de ejecución de scripts en PowerShell | Ejecuta `Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned` |

---

## Despliegue

- **Demo rápida:** exponer el servidor local con un túnel (`cloudflared tunnel --url http://localhost:8000` o `ngrok http 8000`).
- **Hosting:** Render para el backend y Vercel para el frontend. Comando de inicio:
  ```
  uvicorn main:app --host 0.0.0.0 --port $PORT
  ```
  Recuerda agregar la URL del frontend a `ALLOWED_ORIGINS` (CORS). En planes gratuitos el disco es efímero, por lo que SQLite debe sembrarse al arrancar o migrarse a PostgreSQL.

---

## Hoja de ruta

- [ ] Endpoint de validación previa a la carga (aduana): cuarentena de duplicados, monedas inválidas, signos invertidos y cuentas huérfanas.
- [ ] Explicación de desviaciones con causa raíz en la interfaz.
- [ ] Control de acceso por roles (administrador, gerencia, gerente de sucursal, contabilidad).
- [ ] Migración a PostgreSQL.
- [ ] Captura digital de documentos físicos (OCR).
- [ ] Integración con APIs bancarias y sistemas contables.
- [ ] Tasas de cambio oficiales por periodo.

---

## Equipo

Proyecto de Build & Pitch desarrollado por un equipo de dos personas: backend y motor financiero (Python / FastAPI) y frontend / experiencia de usuario (React).

## Licencia

Proyecto de hackathon con datos ficticios. Define la licencia antes de publicarlo de forma abierta.
