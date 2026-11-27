# Revisión Técnica del Sanitizer Integrado (`REVISION_SANITIZER.md`)

Se auditó `backend/app/services/sanitizer_service.py` y `backend/tests/unit/test_sanitizer.py` tras la integración selectiva desde `connection-adjustments` (`e038e8e`).

---

## 1. Hallazgos de Revisión Técnica (Tarea 3)

### a) Correctitud funcional
1. **Fallo de importación sin `presidio_analyzer` / `es_core_news_md` *(Corregido)*:**
   El código original de Rama B instanciaba `NlpEngineProvider` y `AnalyzerEngine` de manera incondicional al importar el módulo. En entornos sin el modelo spaCy (CI ligera o entorno unitario local), cualquier `import app.main` o `pytest tests/unit/test_sanitizer.py` fallaba con `ModuleNotFoundError`.
2. **Falso positivo en montos numéricos (`{1,3}` → `{2,3}`) *(Corregido)*:**
   La expresión original `\b\d{1,3}(?:[.,]\d{3}){1,3}\b` capturaba cifras cotidianas de dinero o cantidades con un solo separador de miles (ej. `"50.000 pesos"`, `"1.500 unidades"`) como si fueran `CO_CEDULA`. Se ajustó a `{2,3}` para exigir al menos dos grupos de miles (`7–10` dígitos cuando llevan punto/coma), eliminando falsos positivos sin perder cobertura en cédulas (`1.234.567` a `1.023.456.789`).
3. **Bug en prefijo `+57` de teléfonos *(Corregido)*:**
   El patrón original `\b(?:\+?57[\s\-]?)?3...` colocaba `\b` antes de un `+` opcional; como `+` no es carácter de palabra, `\b` no coincidía después de espacio y dejaba el `"+57 "` sin enmascarar (`"+57 [MASKED_PHONE]"`). Se reemplazó por `(?<!\w)(?:\+?57[\s.\-]?)?`.
4. **Cobertura faltante de direcciones exactas y fijos *(Corregido)*:**
   Se agregó el reconocedor `CO_ADDRESS` (`[MASKED_ADDRESS]`) para direcciones colombianas con nomenclatura numérica real (`Carrera 15 # 80-12`, `Calle 72 No. 10-34`), así como soporte para indicativos fijos `601–608` y separadores por punto.
5. **Placeholders del banco, delimitadores v2, idempotencia y casos borde *(Verificado)*:**
   - Placeholders `C.C. XXX`, `NIT XXX.XXX.XXX-X`, `carrera XX # XX-XX`, `teléfono XXX-XXXXXXX`, `radicado 2025-XXXXX` pasan intactos (0 falsos positivos en los 120 textos de `banco_pqrs_sintetico.json`).
   - Delimitadores `<<<SMRT_PQRS_8F4D_INI>>>` / `<<<SMRT_PQRS_8F4D_FIN>>>` intactos.
   - Idempotencia (`sanitize_text(sanitize_text(x)) == sanitize_text(x)`), `None`, `""`, textos `> 2.000` chars, Unicode/emojis y regionalismos colombianos verificados.

### b) Integración con el flujo actual (`ticket_service.py` y HU-17)
- **Orden de invocación confirmado:** En `backend/app/services/ticket_service.py`, `create_ticket()` ejecuta `sanitized_text = sanitize_text(free_text)` **antes** de `classify_ticket_text(sanitized_text)`.
- **Preservación de texto crudo para auditoría:** `ticket.original_text` guarda `free_text` intacto; `create_ai_audit()` persiste tanto `original_text=free_text` como `sanitized_text=sanitized_text` junto con `raw_response` (`JSONB` en `ai_audits` / vista `auditoria_ia` de HU-17). No destruye evidencia original.
- **Compatibilidad con `classifier.py` / Prompt v2:** al integrarse `sanitize_text()` antes de envolver el texto en `USER_DATA_TEMPLATE`, los marcadores `[MASKED_*]` son interpretados de forma limpia sin interferir con el esquema `PromptV2Output`.

### c) Seguridad
- **Alcance del sanitizer:** `sanitizer_service.py` se enfoca exclusivamente en **anonimización de PII** (no implementa filtros ni bloqueos de *prompt injection*, responsabilidad delegada correctamente al bloque `[SEGURIDAD]` de `prompt_mejorado_v2.txt` y a la sanitización de delimitadores en `recomendaciones_integracion.md`).
- **Coherencia con allowlist `[QA-SEC-TEST]`:** verificado mediante prueba unitaria que `[QA-SEC-TEST]` y frases de prueba no son modificados ni corrompidos.
- **Resistencia frente a ofuscación simple *(Corregido)*:** se ampliaron los patrones para cubrir cédulas con espacios entre dígitos (`"1 0 2 3 4 5 6 7 8 9"`) o por bloques (`"1 023 456 789"`), puntos (`"1.023.456"`), teléfonos con guiones (`"310-555-1234"`) o puntos (`"310.555.1234"`), y NIT sin puntos ni guion (`"900123456-7"`).

### d) Pruebas
- Se conservaron las 17 pruebas originales de Rama B en `backend/tests/unit/test_sanitizer.py`.
- Las 5 pruebas que ejercitan detección NER real de nombres (`PERSON`) mediante spaCy se condicionaron con `@pytest.mark.skipif(not _PRESIDIO_AVAILABLE, ...)` para no romper CI sin el modelo `es_core_news_md`.
- Se añadieron **8 pruebas unitarias** sin dependencia externa (total **25 casos** en `test_sanitizer.py`), incluyendo pipeline NER mockeado, placeholders del banco, validación sobre los 120 textos del golden set, delimitadores + `[QA-SEC-TEST]`, ofuscación, no sobre-redacción de montos, idempotencia y casos borde (`None`, `""`, `> 2.000` chars, emojis).

---

## 2. Resumen de Parches Aplicados en `sanitizer_service.py`

| Cambio | Motivo | Impacto |
|---|---|---|
| Carga `try/except` de Presidio/spaCy + fallback regex determinista ordenado (`EMAIL` → `PHONE` → `CO_NIT` → `CO_ADDRESS` → `CO_CEDULA`) | Evitar fallo de importación y mantener protección PII sin colisiones entre teléfono y NIT | Alto en portabilidad/CI |
| Ajuste `{1,3}` → `{2,3}` en `CO_CEDULA` + variantes con espacios (`1 0 2 3...` y `1 023...`) | Eliminar falsos positivos en cifras (`50.000`) y bloquear evasión por espacios | Alto en precisión |
| Prefijo `(?<!\w)(?:\+?57[\s.\-]?)?` + fijos `60[1-8]` + puntos en `PHONE_NUMBER` | Corregir residuo `"+57 "` y cubrir `310-555-1234`, `310.555.1234`, `601-555-1234` | Medio-Alto |
| Nuevo entity `CO_ADDRESS` (`[MASKED_ADDRESS]`) | Cubrir direcciones numéricas exactas respetando `carrera XX # XX-XX` | Medio |
| Guard `if not text: return text` en `mask_regex_patterns`, `mask_ner_patterns` y `sanitize_text` | Soporte seguro de `None` y cadenas vacías | Bajo (higiene) |
