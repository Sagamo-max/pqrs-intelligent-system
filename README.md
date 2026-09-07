# Sistema Inteligente de Gestión y Triaje de PQRS

Módulo autónomo para la recepción, clasificación multivariable y direccionamiento automático de Peticiones, Quejas, Reclamos y Sugerencias (PQRS) mediante Inteligencia Artificial y Procesamiento de Lenguaje Natural (PLN).

---

## 🏛️ Contexto Arquitectónico y Legal

- **Cálculo Determinista de Plazos (Ley 1755 de 2015):** Los términos legales de respuesta (10, 15 o 30 días hábiles) son calculados estrictamente por reglas de negocio en el backend; la IA no infiere plazos.
- **Protección de Datos Personales (Ley 1581 de 2012):** Pipeline con sanitización y enmascaramiento previo de PII (Personally Identifiable Information) antes del envío a proveedores externos de IA.
- **Trazabilidad y Auditoría:** Registro inmutable de justificaciones y clasificaciones (automáticas o manuales) en base de datos.
- **Ecosistema Modular:** Triaje estructurado desacoplado, preparado para entrega al módulo complementario de generación de respuestas (RAG).

---

## 🛠️ Stack Tecnológico

- **Lenguaje:** Python 3.11+
- **Framework Web:** FastAPI
- **Base de Datos:** PostgreSQL & SQLAlchemy ORM
- **IA / LLM:** Integración vía Structured Outputs (Gemini / Groq)
- **Servidor ASGI:** Uvicorn

---

## 📂 Estructura del Monorepo

```text
pqrs-intelligent-system/
├── backend/            # API REST en FastAPI, servicios de IA y persistencia
├── frontend/           # Interfaz administrativa web ligera
└── README.md