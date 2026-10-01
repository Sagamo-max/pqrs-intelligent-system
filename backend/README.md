# Backend de triaje de PQRS

API REST construida con FastAPI para registrar PQRS, sanitizar datos personales y solicitar una clasificación estructurada a un modelo compatible con el SDK de OpenAI.

## Componentes

```text
backend/
├── app/
│   ├── core/
│   │   ├── config.py       # Settings desde .env
│   │   └── database.py     # Engine, Base y sesiones SQLAlchemy
│   ├── models/             # Claimant, Department, Ticket y auditorías
│   ├── routers/
│   │   ├── health.py       # Endpoint de salud
│   │   └── ticket.py       # Clasificación y recepción de PQRS
│   ├── schemas/             # DTOs y validaciones Pydantic
│   └── services/
│       ├── audit_service.py
│       ├── claimant_service.py
│       ├── classifier.py
│       ├── sanitizer_service.py
│       ├── sla.py
│       └── ticket_service.py
├── alembic/                 # Historial de esquema
├── alembic.ini
├── requirements.txt
└── README.md
```

## Configuración

`app.core.config.Settings` carga `.env` desde el directorio de ejecución. Copiar `.env.example` a `.env` y reemplazar los valores de ejemplo. Son obligatorias:

```dotenv
AI_API_KEY=tu_api_key
AI_MODEL_NAME=tu_modelo
```

La conexión de PostgreSQL puede configurarse de dos maneras. Se recomienda una URL completa:

```dotenv
DATABASE_URL=postgresql://usuario:password@host:5432/base_de_datos
```

Si `DATABASE_URL` se omite, se construye con estas variables:

```dotenv
POSTGRES_USER=postgres
POSTGRES_PASSWORD=tu_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=ticket_db
```

También se pueden definir:

```dotenv
PROJECT_NAME=Ticket Intelligent Triage API
API_V1_STR=/api/v1
AI_PROVIDER=openai
AI_BASE_URL=https://api.example.com/v1
```

`AI_BASE_URL` es opcional y permite usar un gateway o proveedor compatible con la API de OpenAI.

## Instalación y ejecución

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m spacy download es_core_news_sm
alembic upgrade head
uvicorn app.main:app --reload
```

La aplicación queda en `http://127.0.0.1:8000`. La especificación OpenAPI está en `/docs` y `/redoc`.

## API disponible

### Salud

`GET /`

Respuesta aproximada:

```json
{
  "status": "online",
  "service": "Ticket Triage Backend",
  "version": "0.1.0"
}
```

### Clasificación de prueba

`POST /api/v1/pqrs/classify-poc`

Entrada:

```json
{
  "text": "Texto de la solicitud que contiene al menos 15 caracteres."
}
```

Devuelve una clasificación estructurada con:

- `ticket_type`: `PETITION`, `COMPLAINT`, `CLAIM` o `SUGGESTION`.
- `priority`: `HIGH`, `MEDIUM` o `LOW`.
- `responsible_area`: área responsable, con máximo 20 caracteres.
- `decision_justification`: explicación de la decisión.

Este endpoint envía el texto directamente al clasificador y sirve como prueba de concepto.

### Recepción de PQRS

`POST /api/v1/pqrs/`

Entrada:

```json
{
  "claimant": {
    "full_name": "Nombre completo",
    "document_type": "CC",
    "document_number": "1234567890",
    "email": "persona@example.com",
    "phone": "3001234567"
  },
  "free_text": "Descripción de la petición con al menos 15 caracteres."
}
```

Flujo actual:

1. Busca o crea el ciudadano por número de documento.
2. Crea el ticket con número `PQRS-XXXXXXXX`.
3. Sanitiza correo, teléfono, documento y entidades de persona.
4. Envía el texto sanitizado al modelo.
5. Guarda la clasificación y los textos en `ai_audits`.
6. Devuelve el número de seguimiento y el estado.

Respuesta:

```json
{
  "ticket_number": "PQRS-1A2B3C4D",
  "status": "RECEIVED"
}
```

## Persistencia

Las migraciones crean las tablas:

- `claimants`: datos del solicitante.
- `departments`: áreas responsables.
- `tickets`: solicitud, estado, prioridad, fechas y relaciones.
- `ai_audits`: modelo, proveedor, texto original, texto sanitizado y clasificación sugerida.
- `change_audits`: estructura preparada para registrar cambios manuales.

Comandos habituales:

```powershell
alembic current
alembic history
alembic upgrade head
alembic downgrade -1
```

## Estados y reglas actuales

Estados de ticket: `RECEIVED`, `IN_PROGRESS`, `RESOLVED`, `CLOSED`.

Tipos: `PETITION`, `COMPLAINT`, `CLAIM`, `SUGGESTION`.

Prioridades: `HIGH`, `MEDIUM`, `LOW`.

El servicio SLA actual devuelve la fecha de hoy más 15 días calendario, independientemente del tipo recibido. La clasificación de IA se guarda como sugerencia en auditoría; no actualiza todavía los campos principales del ticket.

## Limitaciones conocidas

- No hay pruebas automatizadas en el repositorio.
- No hay autenticación ni autorización.
- No existe endpoint de consulta, actualización o cierre de tickets.
- La configuración de PostgreSQL no admite todavía una URL completa configurable.
- El clasificador está acoplado al cliente de OpenAI aunque existe `AI_PROVIDER` en configuración.
- Las excepciones se devuelven en el detalle HTTP y el flujo de creación realiza varios commits antes de completar todo el proceso.
- `spacy.load("es_core_news_sm")` exige que el modelo de idioma esté instalado antes de importar el sanitizador.