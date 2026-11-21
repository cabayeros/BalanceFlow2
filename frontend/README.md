# BalanceFlow frontend

Interfaz React para el API de BalanceFlow.

## Requisitos

- Node.js 22.19 o superior.
- Backend de BalanceFlow disponible en `http://localhost:8000`.

## Instalación y desarrollo en Windows PowerShell

Desde la carpeta `frontend`:

```powershell
npm.cmd install
npm.cmd run dev
```

Abre la URL local que muestre Vite (normalmente `http://localhost:5173`). Se usa `npm.cmd` para evitar las restricciones de ejecución de scripts de PowerShell que pueden bloquear `npm.ps1`.

La configuración local de npm limita los reintentos y el tiempo de espera del registro para mostrar los errores de conexión más rápido.

## Error de certificado al instalar

Si npm muestra `UNABLE_TO_VERIFY_LEAF_SIGNATURE` o `unable to verify the first certificate`, la conexión al registro npm está usando una CA que Node no reconoce. No desactives `strict-ssl`.

En una red que instala su CA en el almacén de certificados de Windows, prueba:

```powershell
$env:NODE_USE_SYSTEM_CA = '1'
npm.cmd install
```

Si persiste, instala la CA raíz oficial de la red en **Entidades de certificación raíz de confianza** de Windows o solicita a TI el certificado PEM. Con un archivo PEM de confianza:

```powershell
$env:NODE_EXTRA_CA_CERTS = 'C:\ruta\certificados\ca-red.pem'
npm.cmd install
```

## Configuración de la API

La aplicación usa `http://localhost:8000` por defecto. Si el backend está en otra dirección, copia `.env.example` a `.env` y configura `VITE_API_URL`, por ejemplo:

```env
VITE_API_URL=http://localhost:8000
```

La aplicación consume `/api/empresas`, `/api/sucursales`, `/api/transacciones`, `/api/uploads/excel` y `/api/consolidacion/resumen`. La descarga de reportes requiere `/api/exportar/excel`.
