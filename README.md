# PQRS Intelligent System

Sistema para recibir, sanitizar, clasificar y dar trazabilidad a Peticiones, Quejas, Reclamos y Sugerencias (PQRS). El backend expone una API FastAPI, usa PostgreSQL para persistencia y OpenAI para el triaje inteligente.

[![Tests](https://github.com/Sagamo-max/pqrs-intelligent-system/actions/workflows/test.yml/badge.svg)](https://github.com/Sagamo-max/pqrs-intelligent-system/actions/workflows/test.yml)

## Stack

- Python 3.12+
- FastAPI, SQLAlchemy 2.0, Pydantic v2 y Alembic
- PostgreSQL 16
- OpenAI
- Docker Compose

## Inicio rápido

Requiere Docker Desktop:

```bash
docker compose up -d
```

La API queda disponible en `http://localhost:8000` y PostgreSQL en `localhost:5432`.

## Estructura del repositorio

```text
pqrs-intelligent-system/
├── backend/           # API, migraciones y pruebas
├── docker-compose.yml # Servicios api y db
├── .github/           # Workflows de CI/CD
└── frontend/          # Espacio para la interfaz
```

Consulta el [README del backend](backend/README.md) para la configuración local, Docker, variables de entorno, pruebas y migraciones.
