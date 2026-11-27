# Integración Controlada del Sanitizer (`connection-adjustments` → `smartpqrs_auditoria_banco_pruebas`)

## 1. Diagnóstico de Divergencias y Topología Git

- **Rama A (actual):** `smartpqrs_auditoria_banco_pruebas` (`e207af3`)
- **Rama B (pendiente):** `connection-adjustments` (`e038e8e`)
- **Ancestro común:** `main` (`1174f26` — *Merge pull request #15 from Sagamo-max/frontend-implementation*)

> **Nota sobre el alcance real de Rama B:** La rama `connection-adjustments` no contiene un módulo de archivos adjuntos (*attachments*); comprende dos commits orientados a (1) integración con API externa/eventos ("Compañero" + tabla `outbox_events` + `organizaciones`) y (2) mejoras al servicio de sanitización PII colombiano.

### Commits en Rama B (`1174f26..e038e8e`)

| Commit | Descripción | Archivos | Decisión |
|---|---|---:|---|
| `eceb430` | `feat: Add outbox events table and integrate with ticket creation` | 31 | **Solo extracción selectiva** de `backend/scripts/diagnose_sanitizer.py` y el test de corchetes en `test_sanitizer.py`; el resto corresponde a outbox/Compañero y colisiona con Rama A. |
| `e038e8e` | `feat(sanitizer): enhance PII masking for Colombian documents and add tests` | 3 | **Integración selectiva** de `sanitizer_service.py` y `test_sanitizer.py`; se **excluyó** `backend/tests/conftest.py` porque depende de `settings.COMPANERO_API_ENABLED` definido en `eceb430`. |

---

## 2. Clasificación de Archivos (`git diff --stat smartpqrs_auditoria_banco_pruebas..connection-adjustments`)

### a) Solo Sanitizer (**Integrados selectivamente**)
- `backend/app/services/sanitizer_service.py` *(traído desde `e038e8e`)*
- `backend/tests/unit/test_sanitizer.py` *(traído desde `e038e8e`, incluye el aporte de `eceb430`)*
- `backend/scripts/diagnose_sanitizer.py` *(traído desde `e038e8e` / `eceb430`)*

### b) Integración Externa "Compañero" / Outbox / Organizaciones (**NO traídos**)
- Modelos y migraciones: `backend/app/models/organizacion.py`, `backend/app/models/outbox_event.py`, `backend/alembic/versions/b7d4e9f1a2c3_add_outbox_events_table.py`, `c8e5f2a1b4d6_add_organization_id_to_tickets.py`, `d9f6a3b8c2e1_add_organizaciones_table.py`.
- Servicios, routers y esquemas: `backend/app/services/companero_client.py`, `event_publisher.py`, `routers/events.py`, `routers/integration.py`, `routers/organizacion.py`, `schemas/events.py`, `schemas/organizacion.py`.
- Configuración, scripts, frontend y pruebas de Compañero: `backend/.env.example`, `backend/README.md`, `backend/app/core/config.py`, `backend/requirements.txt` (`httpx>=0.27`), `docker-compose.yml`, `frontend/app.py`, `backend/scripts/diagnose_companero_payload.py`, `backend/tests/fixtures/payloads.py`, `backend/tests/integration/test_companero_integration.py`, `test_events.py`, `test_organizaciones_router.py`.

**Motivo de exclusión:** introducen una integración externa fuera del alcance del sanitizer, añaden 3 migraciones Alembic que bifurcan desde `a1b2c3d4e5f6` y generarían *multiple heads* junto a `b2c3d4e5f6a7` de HU-17/HU-18, y exigen variables de entorno nuevas (`COMPANERO_API_ENABLED`).

### c) Mixtos o que colisionan con cambios de la Rama A (**NO sobrescritos**)
- `backend/app/main.py`, `backend/app/models/ticket.py`, `backend/app/models/__init__.py`, `backend/app/routers/ticket.py`, `backend/app/schemas/ticket.py`, `backend/app/services/ticket_service.py`: modificados en Rama A por HU-15..HU-19; se preservaron intactos en Rama A.
- `backend/tests/conftest.py`: en `e038e8e` agrega el fixture `autouse` `disable_companero_api_for_tests` (`mocker.patch.object(settings, "COMPANERO_API_ENABLED", False)`), el cual fallaría con `AttributeError` en Rama A porque `COMPANERO_API_ENABLED` no existe en `Settings`. Se preservó el `conftest.py` de Rama A.
- Artefactos exclusivos de Rama A (HU-15..HU-19, `banco_pqrs_sintetico.json/.csv`, `docs/auditoria_prompt/*`, `scripts/validar_banco_pqrs.py`): preservados intactos.

---

## 3. Pasos de Integración Ejecutados

1. Creación de rama de respaldo inmutable:
   ```bash
   git branch backup/ramaA-antes-integracion
   ```
2. Extracción selectiva sin merge ciego:
   ```bash
   git checkout connection-adjustments -- backend/app/services/sanitizer_service.py backend/tests/unit/test_sanitizer.py backend/scripts/diagnose_sanitizer.py
   ```
3. Conflictos encontrados: **0 conflictos de merge**, al haberse evitado el merge completo mediante `git checkout <ramaB> -- <rutas>` y haberse descartado explícitamente el hunk incompatible de `backend/tests/conftest.py`.
