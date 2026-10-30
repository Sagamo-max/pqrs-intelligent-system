# Backend de PQRS Intelligent Triage

Backend para el triaje inteligente de Peticiones, Quejas, Reclamos y Sugerencias (PQRS). Expone una API FastAPI, persiste la información en PostgreSQL y usa OpenAI para proponer la clasificación de cada solicitud.

## Estructura

### Stack técnico

- Python 3.12+
- FastAPI y Uvicorn
- PostgreSQL 16
- SQLAlchemy 2.0 y Alembic
- Pydantic v2
- OpenAI
- pytest y pytest-cov

### Carpetas y archivos principales

```text
backend/
├── app/             # API, modelos, esquemas y servicios
├── alembic/         # Migraciones de base de datos
├── tests/           # Pruebas unitarias y de integración
├── Dockerfile       # Imagen del backend
└── constraints.txt  # Versiones fijadas por seguridad
```

## Local Setup

### Requisitos

- Python 3.12 o superior
- PostgreSQL 16, o Docker
- Docker Desktop

Desde `backend/`, crea y activa un entorno virtual:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

En Linux o Mac:

```bash
source venv/bin/activate
```

Instala las dependencias:

```bash
pip install -r requirements-dev.txt
```

Configura `.env` copiando `backend/.env.example` y reemplazando los valores de ejemplo. Después aplica las migraciones y ejecuta la API:

```bash
alembic upgrade head
uvicorn app.main:app --reload
```

La API queda disponible en `http://localhost:8000`.

Ejecuta las pruebas con:

```bash
pytest -v
```

## Docker

### Requisitos

- Docker Desktop 4.x o superior
- Docker Compose 2.x o superior

Desde la raíz del repositorio, inicia todos los servicios:

```bash
docker compose up -d
```

Verifica que `api` y `db` estén `healthy`:

```bash
docker compose ps
```

- API: `http://localhost:8000`
- PostgreSQL: `localhost:5432`

Comandos útiles:

```bash
docker compose logs -f api
docker compose up -d --build api
docker compose exec api alembic upgrade head
docker compose exec db psql -U postgres -d ticket_db
docker compose down
docker compose down -v
```

El servicio `api` ejecuta `alembic upgrade head` automáticamente al arrancar mediante `command:` en `docker-compose.yml`.

## Variables de entorno

| Variable | Requerida | Valor por defecto | Descripción |
|---|---:|---|---|
| `DATABASE_URL` | Sí | — | URL de conexión a PostgreSQL |
| `TEST_DATABASE_URL` | Sí para tests | — | URL de una base de datos PostgreSQL aislada para pruebas |
| `OPENAI_API_KEY` | Sí | — | Clave del proveedor de IA |
| `AI_PROVIDER` | No | `openai` | Proveedor de clasificación |
| `AI_MODEL_NAME` | Sí | — | Modelo usado para clasificar |
| `AI_BASE_URL` | No | — | URL base opcional para un proveedor compatible |
| `PROJECT_NAME` | No | `Ticket Intelligent Triage API` | Nombre del proyecto |
| `API_V1_STR` | No | `/api/v1` | Prefijo de la API |

Nunca hardcodees valores reales ni subas `.env` al repositorio.

## Seguridad

- `constraints.txt` fija versiones de dependencias transitivas con CVEs conocidos (`msgpack`, `urllib3` y `setuptools`).
- El `Dockerfile` ejecuta `apt-get upgrade` en el stage runtime para aplicar parches de Debian.
- El servicio `api` corre como usuario no-root (`appuser`).
- `.env` está incluido en `.gitignore` y nunca debe subirse al repositorio.
- `tests/conftest.py` rechaza la ejecución si `TEST_DATABASE_URL` es igual a `DATABASE_URL`.

## Tests

Las pruebas requieren PostgreSQL; no usan SQLite porque los modelos utilizan `JSONB` y `UUID`.

`TEST_DATABASE_URL` es obligatoria y debe apuntar a una base de datos aislada:

```bash
pytest -v
```

Para obtener cobertura:

```bash
pytest --cov=app --cov-report=term-missing
```

## Migrations

```bash
alembic upgrade head
alembic revision -m "..."
alembic current
alembic history
```

Nunca dejes `<auto>` en un archivo de migración.

## CI/CD

El workflow de GitHub Actions en `.github/workflows/test.yml` ejecuta:

- `test`: instala dependencias, prepara PostgreSQL, ejecuta migraciones y corre pytest con cobertura.
- `docker-build`: construye la imagen y ejecuta un smoke test de la API.

## Known security risks and false positives

### CVE-2026-85091 — `zlib` in Debian 13 trixie (HIGH, no fix available)

- **Package:** `zlib 1:1.3.dfsg+really1.3.1-1` (base image `python:3.12-slim`)
- **Severity:** High (CVSS 7.5)
- **Status:** No patch available from Debian as of 2026-10.
- **Impact:** Buffer overflow when processing maliciously crafted compressed input.
- **Mitigation:** The application does not decompress untrusted user input directly.
  Compression is handled at the HTTP layer by Uvicorn/Starlette. Monitored via
  Debian security advisories; the base image will be updated as soon as a patch
  is released.
- **Reference:** https://scout.docker.com/v/CVE-2026-85091

### `msgpack 1.1.2` flagged by Docker Scout (FALSE POSITIVE)

- **Package:** `msgpack 1.1.2` — reported by `docker scout cves` with 3 HIGH CVEs.
- **Reality:** `msgpack` is **NOT** a dependency of the application. It is
  vendored inside `pip` itself (`pip/_vendor/bom.cdx.json`) and is only used
  by `pip`'s internal SBOM machinery.
- **Verification:**
  ```bash
  docker compose exec api python -c "import msgpack"
  # ModuleNotFoundError: No module named 'msgpack'
  ```
- **Status:** Accepted as a known false positive until `pip` ships a newer
  vendored copy. Tracked for future `pip` upgrades.

## Security scanning

### Local scan (requires Docker Scout login)

```bash
docker scout quickview local://pqrs-intelligent-system-api:latest
docker scout cves local://pqrs-intelligent-system-api:latest --only-severity high
```

### Expected results

- `zlib` (1 HIGH): known Debian CVE without patch, documented above.
- `msgpack` (3 HIGH): **false positive**, documented above.
- `urllib3` / `setuptools`: patched via `constraints.txt` (`2.8.0+`, `78.1.1+`).

The image is considered production-ready with these two documented exceptions.

## Roadmap

- HU-14: migrar la sanitización de PII a Microsoft Presidio.
- Añadir autenticación en endpoints admin.
- Fusionar con el módulo del compañero mediante un monolito modular por eventos.
