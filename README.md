# PQRS Intelligent System

Sistema para recibir, sanitizar, clasificar y dar trazabilidad a Peticiones, Quejas, Reclamos y Sugerencias (PQRS). El backend expone una API FastAPI con PostgreSQL y OpenAI para el triaje inteligente, y el frontend activo está construido en React + Vite + TypeScript + TailwindCSS.

[![Tests](https://github.com/Sagamo-max/pqrs-intelligent-system/actions/workflows/test.yml/badge.svg)](https://github.com/Sagamo-max/pqrs-intelligent-system/actions/workflows/test.yml)

## Stack

- **Backend:** Python 3.12+, FastAPI, SQLAlchemy 2.0, Pydantic v2, Alembic, PostgreSQL 16, Presidio + spaCy, OpenAI
- **Frontend activo (`frontend/`):** React 18, Vite, TypeScript, TailwindCSS v3, shadcn/ui (Radix), TanStack Query v5, Zustand, React Hook Form + Zod, Recharts
- **Infraestructura:** Docker Compose (desarrollo local) y Railway (servicios independientes para backend y frontend)

## Inicio rápido local

### 1. Backend (API + PostgreSQL)

Requiere Docker Desktop:

```bash
docker compose up -d
```

La API queda disponible en `http://localhost:8000` y PostgreSQL en `localhost:5432`.

### 2. Frontend (React + Vite)

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

La aplicación web queda disponible en `http://localhost:5173`.

## Estructura del repositorio

```text
pqrs-intelligent-system/
├── backend/                   # API FastAPI, migraciones y pruebas
├── frontend/                  # Aplicación web React + Vite + TailwindCSS (activa)
├── frontend_streamlit_legacy/ # Prototipo anterior en Streamlit (archivado como referencia)
├── docker-compose.yml         # Servicios api y db
└── .github/                   # Workflows de CI/CD
```

## Documentación adicional

- **Backend:** [README del backend](backend/README.md) para configuración local, Docker, variables de entorno, pruebas y migraciones.
- **Despliegue del Frontend en Railway:** [frontend/README_DEPLOY.md](frontend/README_DEPLOY.md) con los pasos para desplegar `frontend/` como servicio independiente usando Railpack, `Root Directory=/frontend`, `VITE_API_BASE_URL=https://${{backend.RAILWAY_PUBLIC_DOMAIN}}/api/v1` y configuración de CORS.
