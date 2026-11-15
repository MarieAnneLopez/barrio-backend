# Publicar la API (Render + Neon)

Guía completa, con el frontend, en `docs/PUBLICACION.md` de la carpeta del proyecto. Resumen del backend:

- **Framework:** FastAPI + Uvicorn (Python 3.13).
- **Base de datos:** PostgreSQL con PostGIS (SRID 4326), migraciones con Alembic.
- **Servicios externos en producción:** ninguno obligatorio.
  - El mapa usa capas propias en `seed/base/`, sin teselas externas.
  - El ETL contra OSM y Datos Abiertos solo corre en desarrollo; producción carga `seed/`.
  - El chat corre en modo Local (`CHAT_MODEL=analitico`), sin la API de Anthropic.

## Arranque (`render.yaml`)

```
build:  pip install -r requirements.txt
start:  python -m etl.bootstrap && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

`etl/bootstrap.py` hace esto en cada arranque:
1. valida la cuenta de administración;
2. activa PostGIS y aplica las migraciones;
3. carga las semillas de **cada módulo que esté vacío**, para que los id no cambien al reiniciar y una carga cortada se complete en el siguiente arranque. `RESEED_MODULES` fuerza la recarga puntual de unos módulos; hay que quitarla después;
4. recarga la Historia Local y crea o actualiza la cuenta de administración.

## Variables de entorno de producción

Van en el panel de Render; ninguna lleva valores reales en el repositorio.

| Variable | Valor | Nota |
|---|---|---|
| `ENVIRONMENT` | `production` | Apaga `/docs`, exige `JWT_SECRET` y pone la cookie `Secure` |
| `DATABASE_URL` | cadena de Neon con `sslmode=require` | Se copia del panel de Neon |
| `JWT_SECRET` | la genera Render (`generateValue`) | 32 caracteres o más |
| `CORS_ORIGINS` | `["https://<tu-proyecto>.pages.dev"]` | Lista JSON con la URL de Cloudflare Pages |
| `ADMIN_EMAIL` | correo de la cuenta de administración | |
| `ADMIN_PASSWORD` | clave nueva, 12 caracteres o más | La API rechaza la clave de demostración de `.env.example` |
| `PROXY_SECRET` | texto aleatorio largo | El mismo valor va en Cloudflare Pages |
| `CHAT_MODEL` | `analitico` | Sin `ANTHROPIC_API_KEY` en producción |
| `CHAT_MESSAGES_PER_MINUTE` / `_PER_HOUR` | `30` / `120` | Límites del chat por visitante |

El inicio de sesión tiene su propio límite: 10 intentos fallidos cada 15 minutos.
