# Contratos API — Historias de Usuario HU-15 a HU-19

Todos los endpoints requieren autenticación Bearer JWT (`Authorization: Bearer <access_token>`), salvo que se indique un rol mínimo específico. Los identificadores de PQRS aceptan tanto `UUID` (`tickets.id`) como `tracking_number` (ej. `PQRS-A1B2C3D4`).

> **Rutas disponibles:** Las rutas están expuestas bajo `/api/...` (contrato principal) y `/api/v1/...` (versionado del proyecto).

---

## 1. HU-15 — Reasignación manual de área responsable

- **Método y URL:** `PATCH /api/pqrs/{id}/area` (también `PATCH /api/v1/pqrs/{id}/area`)
- **Autenticación / RBAC:** Usuario autenticado (`ANALISTA` solo sobre tickets de su área; `SUPERVISOR` y `MASTER` sobre cualquier ticket).
- **Regla de negocio:** Actualiza únicamente `area_id` y registra trazabilidad en `change_audits` (`auditoria_cambios`). **No altera** `status`, `ticket_type`, `due_date` ni `needs_sla_validation`.

### Request Body (`application/json`)

Acepta `area_id` o su alias `id_area`, y `change_reason` o su alias `motivo`:

```json
{
  "area_id": "22222222-2222-2222-2222-222222222222",
  "change_reason": "El caso corresponde a cobros y facturación",
  "responsible_user": "supervisor.pqrs"
}
```

### Response `200 OK`

```json
{
  "id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
  "tracking_number": "PQRS-1A2B3C4D",
  "status": "RECEIVED",
  "ticket_type": "CLAIM",
  "priority": "HIGH",
  "filing_date": "2026-11-20",
  "due_date": "2026-12-11",
  "needs_sla_validation": false,
  "area": {
    "id": "22222222-2222-2222-2222-222222222222",
    "code": "FACTURACION",
    "name": "Facturación"
  }
}
```

### Errores posibles
- `400 Bad Request`: el área destino está inactiva o el ticket ya pertenece a esa área.
- `401 Unauthorized`: token ausente o inválido.
- `404 Not Found`: PQRS o área destino inexistente.
- `422 Unprocessable Entity`: payload inválido.

---

## 2. HU-16 — Detalle y seguimiento individual de PQRS

- **Método y URL:** `GET /api/pqrs/{id}` (también `GET /api/v1/pqrs/{id}`)
- **Autenticación / RBAC:** Usuario autenticado (`ANALISTA` restringido a su área).
- **Regla de negocio:** Consulta `tickets` con joins sobre `claimants`, `areas`, `ai_audits` y `change_audits` (con `funcionarios`). Devuelve datos del solicitante, texto original, clasificación/justificación IA, estado SLA y línea de tiempo cronológica diferenciando visualmente decisiones IA (`source_type: "AI_DECISION"`, `visual_badge: "IA"`) de intervenciones humanas (`source_type: "HUMAN_INTERVENTION"`, `visual_badge: "HUMANO"`).

### Response `200 OK`

```json
{
  "id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
  "tracking_number": "PQRS-1A2B3C4D",
  "original_text": "Me cobraron doble la factura del mes pasado.",
  "ticket_type": "CLAIM",
  "priority": "HIGH",
  "status": "IN_PROGRESS",
  "created_at": "2026-11-20T10:00:00Z",
  "updated_at": "2026-11-21T09:15:00Z",
  "claimant": {
    "id": "33333333-3333-3333-3333-333333333333",
    "document_type": "CC",
    "document_number": "1020304050",
    "first_name": "Laura",
    "last_name": "Gómez",
    "email": "laura.gomez@ejemplo.co",
    "phone": "3001112233"
  },
  "area": {
    "id": "22222222-2222-2222-2222-222222222222",
    "code": "FACTURACION",
    "name": "Facturación"
  },
  "sla": {
    "filing_date": "2026-11-20",
    "due_date": "2026-12-11",
    "needs_sla_validation": false,
    "alert_level": "NORMAL",
    "days_remaining": 15,
    "is_overdue": false
  },
  "clasificacion_ia": {
    "id": "44444444-4444-4444-4444-444444444444",
    "ai_model": "gpt-6-luna",
    "provider": "openai",
    "classification_source": "openai",
    "suggested_type": "CLAIM",
    "suggested_priority": "HIGH",
    "suggested_area_code": "FACTURACION",
    "decision_justification": "Cobro duplicado reportado por el usuario; requiere devolución o ajuste.",
    "confidence": 0.96,
    "created_at": "2026-11-20T10:00:02Z"
  },
  "justificacion_ia": "Cobro duplicado reportado por el usuario; requiere devolución o ajuste.",
  "timeline": [
    {
      "event_id": "44444444-4444-4444-4444-444444444444",
      "source_type": "AI_DECISION",
      "visual_badge": "IA",
      "timestamp": "2026-11-20T10:00:02Z",
      "actor": "IA (openai/gpt-6-luna)",
      "actor_id": null,
      "title": "Clasificación automática (openai)",
      "description": "Cobro duplicado reportado por el usuario; requiere devolución o ajuste.",
      "modified_field": null,
      "old_value": null,
      "new_value": "tipo=CLAIM, prioridad=HIGH, area=FACTURACION",
      "details": {
        "modelo": "gpt-6-luna",
        "proveedor": "openai",
        "fuente": "openai",
        "confianza": 0.96
      }
    },
    {
      "event_id": "55555555-5555-5555-5555-555555555555",
      "source_type": "HUMAN_INTERVENTION",
      "visual_badge": "HUMANO",
      "timestamp": "2026-11-21T09:15:00Z",
      "actor": "Supervisor Principal",
      "actor_id": "66666666-6666-6666-6666-666666666666",
      "title": "Intervención manual: AREA_REASSIGNMENT",
      "description": "El caso corresponde a cobros y facturación",
      "modified_field": "area_id",
      "old_value": "ATENCION_USUARIO",
      "new_value": "FACTURACION",
      "details": {
        "responsible_user": "supervisor.pqrs",
        "event_type": "AREA_REASSIGNMENT"
      }
    }
  ]
}
```

### Errores posibles
- `401 Unauthorized`: token ausente o inválido.
- `404 Not Found`: PQRS inexistente o fuera del alcance del `ANALISTA`.

---

## 3. HU-17 — Auditoría de decisión IA

- **Método y URL:** `GET /api/pqrs/{id}/auditoria-ia` (también `GET /api/v1/pqrs/{id}/auditoria-ia`)
- **Autenticación / RBAC:** Requiere rol mínimo `SUPERVISOR` (`SUPERVISOR` o `MASTER`). `ANALISTA` recibe `403 Forbidden`.
- **Persistencia automática:** Cada clasificación exitosa inserta en `ai_audits` (vista `auditoria_ia`) con `raw_response`, `decision_justification`, `ai_model` y `created_at`.

### Response `200 OK`

Lista ordenada cronológicamente (`created_at ASC`):

```json
[
  {
    "id": "44444444-4444-4444-4444-444444444444",
    "ticket_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
    "provider": "openai",
    "ai_model": "gpt-6-luna",
    "original_text": "Me cobraron doble la factura...",
    "sanitized_text": "Me cobraron doble la factura...",
    "decision_justification": "Cobro duplicado reportado; corresponde a reclamo en facturación.",
    "suggested_type": "CLAIM",
    "suggested_priority": "HIGH",
    "suggested_area_code": "FACTURACION",
    "confidence": 0.96,
    "tokens_used": 180,
    "latency_ms": 420,
    "raw_response": {
      "id": "chatcmpl-xyz",
      "choices": []
    },
    "created_at": "2026-11-20T10:00:02Z"
  }
]
```

### Errores posibles
- `401 Unauthorized`: token ausente o inválido.
- `403 Forbidden`: rol inferior a `SUPERVISOR` (ej. `ANALISTA`).
- `404 Not Found`: PQRS inexistente.

---

## 4. HU-18 — Auditoría de intervenciones humanas

Las modificaciones manuales sobre una PQRS registran automáticamente en `change_audits` (vista `auditoria_cambios`) el `funcionario_id`, `responsible_user`, `modified_field`, `old_value`, `new_value`, `change_reason` y `created_at`:
- **Tipo:** `PATCH /api/pqrs/{id}/tipo` (`modified_field = "ticket_type"`, recalcula SLA).
- **Área:** `PATCH /api/pqrs/{id}/area` (`modified_field = "area_id"`, no altera SLA ni estado).
- **Prioridad:** `PATCH /api/pqrs/{id}/prioridad` (`modified_field = "priority"`, no altera SLA ni estado).

### Request Body (`PATCH /api/pqrs/{id}/prioridad`)

Acepta `priority` o su alias `prioridad`:

```json
{
  "priority": "HIGH",
  "change_reason": "Adulto mayor con afectación directa del servicio",
  "responsible_user": "analista.centro"
}
```

### Response `200 OK`

Retorna `TicketResponse` actualizado con la nueva prioridad.

### Errores posibles
- `400 Bad Request`: la prioridad enviada coincide con la actual.
- `404 Not Found`: PQRS inexistente.
- `422 Unprocessable Entity`: prioridad fuera del enum (`HIGH`, `MEDIUM`, `LOW`).

---

## 5. HU-19 — Dashboard de métricas básicas

- **Método y URL:** `GET /api/dashboard/metricas` (también `GET /api/v1/dashboard/metricas`)
- **Autenticación / RBAC:** Usuario autenticado (`ANALISTA` visualiza métricas agregadas de su área; `SUPERVISOR` y `MASTER` visualizan métricas globales).
- **Implementación:** Consultas SQL en tiempo real con `COUNT` y `GROUP BY` sobre `tickets` y `areas`.

### Response `200 OK`

```json
{
  "total_pqrs": 25,
  "por_tipo": {
    "PETITION": 8,
    "COMPLAINT": 6,
    "CLAIM": 7,
    "SUGGESTION": 4
  },
  "por_area": [
    {
      "area_id": "22222222-2222-2222-2222-222222222222",
      "area_code": "FACTURACION",
      "area_name": "Facturación",
      "total": 10
    },
    {
      "area_id": "11111111-1111-1111-1111-111111111111",
      "area_code": "ATENCION_USUARIO",
      "area_name": "Atención al Usuario",
      "total": 15
    }
  ],
  "por_prioridad": {
    "HIGH": 9,
    "MEDIUM": 11,
    "LOW": 5
  },
  "cumplimiento_sla": {
    "vencidas": 3,
    "a_tiempo": 20,
    "sin_fecha_sla": 2,
    "porcentaje_a_tiempo": 86.96
  },
  "generated_at": "2026-11-26T21:10:00Z"
}
```
