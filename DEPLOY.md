# Despliegue de BalanceFlow

El frontend se publica en Vercel y el backend con PostgreSQL en Render. El archivo `render.yaml` define la API, la base de datos y la carga inicial de datos demo.

## 1. Publicar API y base de datos en Render

1. Sube el repositorio a GitHub.
2. En Render, selecciona **New > Blueprint** y conecta el repositorio.
3. Render detectará `render.yaml`. Revisa y crea `balanceflow-api` y `balanceflow-db`.
4. Espera a que el deploy esté listo. La API tendrá una URL parecida a `https://balanceflow-api.onrender.com`.
5. Comprueba `https://TU-API.onrender.com/health` y verifica que responda con `status: healthy` y `database: conectada`.

El hook de primer deploy ejecuta `seed.py` una vez para cargar la base demo. No lo configures para que corra en cada deploy: el seed borra los datos existentes.

## 2. Publicar el frontend en Vercel

1. En Vercel, selecciona **Add New > Project** e importa el mismo repositorio.
2. En **Root Directory**, selecciona `frontend`.
3. Usa **Vite** como preset. Los valores deben ser:
   - Build Command: `npm run build`
   - Output Directory: `dist`
   - Install Command: `npm install`
4. Añade `VITE_API_URL` con la URL pública de la API, sin `/` final; por ejemplo `https://balanceflow-api.onrender.com`.
5. Despliega. Vercel asignará un dominio `*.vercel.app`.

`VITE_API_URL` se incorpora durante el build. Si la cambias, vuelve a desplegar el frontend.

## 3. Autorizar el dominio del frontend en Render

En Render, abre `balanceflow-api` > **Environment** y añade `ALLOWED_ORIGINS` con un arreglo JSON que contenga el dominio exacto de Vercel:

```json
["https://TU-PROYECTO.vercel.app"]
```

Si también vas a usar un dominio propio, incluye ambos orígenes:

```json
["https://TU-PROYECTO.vercel.app", "https://www.tu-dominio.com"]
```

Guarda los cambios y espera el redeploy de la API. Cambia esta variable después de conocer el dominio final de Vercel.

## 4. Dominio propio

Vercel asigna un dominio `vercel.app` automáticamente. Para usar un dominio propio, añádelo en el proyecto de Vercel en **Settings > Domains** y configura los registros DNS que Vercel indique en el proveedor donde compraste el dominio. Después agrega ese mismo origen a `ALLOWED_ORIGINS` en Render y vuelve a desplegar la API.

## Consideraciones del plan gratuito

- Render suspende los servicios web gratuitos tras 15 minutos sin tráfico; la siguiente petición puede tardar alrededor de un minuto mientras el servicio despierta.
- La base Postgres gratuita de Render vence a los 30 días. Para conservar los datos demo más tiempo, usa un plan de base de datos que no venza o exporta los datos antes de esa fecha.
- No ejecutes `python seed.py` manualmente contra una base que ya tenga datos que quieras conservar.
