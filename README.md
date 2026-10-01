# Sistema inteligente de gestión y triaje de PQRS

Repositorio para la recepción, clasificación y trazabilidad de Peticiones, Quejas, Reclamos y Sugerencias (PQRS). La primera iteración implementa un backend FastAPI que recibe una solicitud, protege datos personales antes de enviarla al proveedor de IA y registra la decisión generada.

## Estado actual

El proyecto se encuentra en una fase temprana de backend funcional:

- API FastAPI con endpoint de salud, clasificación aislada y recepción de PQRS.
- Persistencia PostgreSQL mediante SQLAlchemy y migraciones Alembic.
- Registro de ciudadanos, tickets y auditoría de decisiones de IA.
- Sanitización de correos, teléfonos, documentos y entidades de persona antes de la clasificación.
- Integración actual del clasificador con el SDK de OpenAI y salidas estructuradas de Pydantic.
- `frontend/` todavía no contiene una aplicación implementada.

La clasificación se registra en `ai_audits`. En el flujo actual de recepción, el ticket se crea inicialmente como `PETITION` y con prioridad `MEDIUM`; la respuesta del modelo todavía no actualiza esos campos ni asigna un departamento al ticket.

## Principios funcionales

- **Privacidad:** el texto sanitizado es el que se envía al modelo; el texto original y el sanitizado quedan asociados en la auditoría.
- **Trazabilidad:** se conserva el proveedor, modelo, justificación y clasificación sugerida por la IA.
- **Separación de responsabilidades:** routers, servicios, esquemas, modelos y migraciones están organizados por capa.
- **Reglas de negocio explícitas:** el cálculo de vencimiento está aislado en `services/sla.py`. La implementación actual suma 15 días calendario y debe validarse antes de considerarse cálculo legal de días hábiles.

## Tecnologías

- Python 3.11 o superior
- FastAPI y Uvicorn
- Pydantic Settings
- SQLAlchemy 2 y PostgreSQL
- Alembic
- OpenAI Structured Outputs
- spaCy con el modelo `es_core_news_sm`

## Estructura

```text
pqrs-intelligent-system/
├── backend/
│   ├── app/
│   │   ├── core/       # configuración y conexión a PostgreSQL
│   │   ├── models/     # entidades SQLAlchemy
│   │   ├── routers/    # endpoints HTTP
│   │   ├── schemas/    # validación de entrada y salida
│   │   └── services/   # clasificación, sanitización, SLA y persistencia
│   ├── alembic/        # migraciones de base de datos
│   ├── requirements.txt
│   └── README.md
├── frontend/
│   └── README.md
└── README.md
```

## Inicio rápido del backend

### Requisitos

- Python 3.11+
- PostgreSQL disponible en `localhost:5432`
- Base de datos `ticket_db`
- Una clave de API y un modelo compatibles con la integración de OpenAI

Desde `backend/`, crear y activar un entorno virtual:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m spacy download es_core_news_sm
```

Copiar `backend/.env.example` a `backend/.env` y reemplazar los valores de ejemplo:

```dotenv
DATABASE_URL=postgresql://postgres:tu_password@localhost:5432/ticket_db
AI_API_KEY=tu_api_key
AI_MODEL_NAME=tu_modelo
AI_PROVIDER=openai
```

`DATABASE_URL` tiene prioridad. Como alternativa, se pueden definir por separado `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT` y `POSTGRES_DB`. `AI_BASE_URL` es opcional para gateways compatibles con OpenAI. No versionar `.env` ni incluir claves reales en documentación.

Aplicar las migraciones y arrancar la API:

```powershell
alembic upgrade head
uvicorn app.main:app --reload
```

La documentación interactiva de FastAPI queda disponible en `http://127.0.0.1:8000/docs`.

Para más detalle sobre rutas, payloads, configuración y migraciones, consultar [backend/README.md](backend/README.md).

## Alcance pendiente

- Construir el frontend administrativo.
- Implementar asignación persistente de tipo, prioridad y departamento a partir de la clasificación.
- Completar el cálculo de SLA con días hábiles y reglas por tipo de PQRS.
- Añadir autenticación, autorización y gestión de usuarios.
- Añadir pruebas automatizadas y observabilidad.
- Revisar el manejo transaccional del flujo completo y evitar exponer detalles internos de excepciones en respuestas HTTP.

## Nota legal

Las referencias a la Ley 1755 de 2015 y la Ley 1581 de 2012 describen objetivos de diseño, no constituyen asesoría legal ni certifican cumplimiento normativo. El cálculo de términos y las reglas de protección de datos deben validarse con responsables jurídicos y de seguridad.