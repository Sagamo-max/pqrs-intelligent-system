# Despliegue del Frontend SmartPQRS en Railway

Esta guía describe cómo desplegar el frontend React + Vite (`frontend/`) como un **servicio independiente** dentro del mismo proyecto de Railway donde corre el backend FastAPI (`backend/`).

---

## Arquitectura en Railway

```text
Proyecto Railway: smartpqrs
├── Servicio "backend"   → FastAPI (Root Directory: /backend)
├── Servicio "frontend"  → React + Vite servido con `serve` (Root Directory: /frontend)
└── Servicio "postgres"  → PostgreSQL
```

`frontend/railway.toml` ya está configurado con:

```toml
[build]
builder = "RAILPACK"
buildCommand = "npm ci && npm run build"

[deploy]
startCommand = "npx serve -s dist -l $PORT"
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 3
```

---

## Pasos de despliegue en Railway

1. **Crear o abrir el proyecto** en Railway (por ejemplo `smartpqrs`).
2. **Crear el servicio `frontend`**:
   - Clic en **+ New** → **Empty Service** (o **GitHub Repo**).
   - Renombra el servicio a `frontend`.
3. **Conectar el repositorio**:
   - En `frontend` → **Settings** → **Source** → **Connect Repo** → selecciona el repositorio de GitHub.
4. **Configurar Root Directory**:
   - En `frontend` → **Settings** → **Root Directory** → establece `/frontend`.
5. **Generar dominio público**:
   - En `frontend` → **Settings** → **Networking** → **Generate Domain** (después del primer deploy o antes de enlazar variables).
6. **Configurar variables de entorno en `frontend`**:
   - En `frontend` → **Variables** → añade:
     ```env
     VITE_API_BASE_URL=https://${{backend.RAILWAY_PUBLIC_DOMAIN}}/api/v1
     ```
   - Importante: Vite inyecta `VITE_*` en **tiempo de build** (`npm run build`), por lo que debes hacer **Redeploy** en `frontend` cada vez que cambies `VITE_API_BASE_URL` o cambie el dominio del backend.
7. **Configurar CORS en el servicio `backend`** *(requisito crítico)*:
   - En el servicio `backend` → **Variables** → configura la variable de orígenes permitidos apuntando al dominio público del frontend:
     ```env
     CORS_ORIGINS=https://${{frontend.RAILWAY_PUBLIC_DOMAIN}}
     ```
   - `backend/app/main.py` lee `CORS_ORIGINS` (lista separada por comas; en local permite por defecto `http://localhost:5173,http://localhost:3000`) y la aplica en `CORSMiddleware` con `allow_credentials=True`.
   - Haz **Redeploy** en ambos servicios (`backend` y `frontend`) tras guardar las variables.

---

## Enrutamiento SPA

- En Railway: `npx serve -s dist -l $PORT` habilita el modo SPA (`-s`), redirigiendo cualquier ruta desconocida (`/radicar`, `/admin/dashboard`, etc.) a `index.html`.
- En Netlify (referencia opcional): se incluye `public/_redirects` con `/* /index.html 200`.

---

## Verificación local

1. Levanta el backend en `http://localhost:8000` (ver `backend/README.md`).
2. En `frontend/`, crea `.env` a partir de `.env.example`:
   ```bash
   cp .env.example .env
   ```
3. Instala dependencias y ejecuta en desarrollo:
   ```bash
   npm install
   npm run dev
   ```
4. Para probar el build de producción localmente:
   ```bash
   npm run build
   npm run preview
   ```
