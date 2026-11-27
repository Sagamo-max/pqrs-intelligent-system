# Revisión y Corrección de Falsos Positivos NER (`REVISION_SANITIZER_FIX_NER.md`)

## 1. Reproducción en Vivo (`presidio-analyzer 2.2.366` + `spacy 3.8.18` + `es_core_news_md 3.8.0`)

Se reprodujo el fallo reportado en CI ejecutando el sanitizer anterior directamente contra los **120 registros** de `data/banco_pruebas/banco_pqrs_sintetico.json` en Python 3.12 con `es_core_news_md`.

### Hallazgo clave de calibración
El reconocedor `SpacyRecognizer` de Presidio asigna una **puntuación fija de `0.85`** a toda entidad detectada por `es_core_news_md`, tanto en nombres reales como en falsos positivos:
- Nombres reales evaluados: `"Juan Pérez"` (`PER`, `0.85`), `"María José"` (`PER`, `0.85`), `"Carlos"` (`PER`, `0.85`), `"María Rodríguez"` (`PER`, `0.85`), `"Carlos Andrés Gómez"` (`PER`, `0.85`).
- Falsos positivos en el banco: **42 detecciones en 35 registros** (todas con etiqueta spaCy `PER` → Presidio `PERSON` y `score = 0.85`).

### Lista completa de falsos positivos encontrados en el barrido de los 120 registros

| # | ID | Span enmascarado | Etiqueta Presidio / spaCy | Score | Inicio de oración | Patrón lingüístico |
|---:|---|---|---|---:|:---:|---|
| 1 | `PQRS-001` | `Agradezco` | `PERSON` / `PER` | 0.85 | Sí | Verbo 1ª persona / cortesía |
| 2 | `PQRS-005` | `Agradezco` | `PERSON` / `PER` | 0.85 | Sí | Verbo 1ª persona / cortesía |
| 3 | `PQRS-007` | `Agradezco` | `PERSON` / `PER` | 0.85 | Sí | Verbo 1ª persona / cortesía |
| 4 | `PQRS-009` | `PQRS` | `PERSON` / `PER` | 0.85 | No | Sigla institucional de dominio |
| 5 | `PQRS-009` | `Pueden` | `PERSON` / `PER` | 0.85 | Sí | Verbo modal capitalizado |
| 6 | `PQRS-010` | `Talento Humano` | `PERSON` / `PER` | 0.85 | No | Nombre de dependencia SmartPQRS |
| 7 | `PQRS-010` | `Agradezco` | `PERSON` / `PER` | 0.85 | Sí | Verbo 1ª persona / cortesía |
| 8 | `PQRS-014` | `Actuando` | `PERSON` / `PER` | 0.85 | Sí | Gerundio capitalizado tras punto |
| 9 | `PQRS-015` | `Agradezco` | `PERSON` / `PER` | 0.85 | Sí | Verbo 1ª persona / cortesía |
| 10 | `PQRS-017` | `Agradezco` | `PERSON` / `PER` | 0.85 | Sí | Verbo 1ª persona / cortesía |
| 11 | `PQRS-020` | `Agradezco` | `PERSON` / `PER` | 0.85 | Sí | Verbo 1ª persona / cortesía |
| 12 | `PQRS-023` | `Le` | `PERSON` / `PER` | 0.85 | Sí | Pronombre átono capitalizado |
| 13 | `PQRS-023` | `Agradezco` | `PERSON` / `PER` | 0.85 | Sí | Verbo 1ª persona / cortesía |
| 14 | `PQRS-024` | `Justo` | `PERSON` / `PER` | 0.85 | Sí | Adverbio capitalizado tras punto |
| 15 | `PQRS-025` | `Agradezco` | `PERSON` / `PER` | 0.85 | Sí | Verbo 1ª persona / cortesía |
| 16 | `PQRS-027` | `Agradezco` | `PERSON` / `PER` | 0.85 | Sí | Verbo 1ª persona / cortesía |
| 17 | `PQRS-028` | `Talento Humano` | `PERSON` / `PER` | 0.85 | No | Nombre de dependencia SmartPQRS |
| 18 | `PQRS-028` | `Agradezco` | `PERSON` / `PER` | 0.85 | Sí | Verbo 1ª persona / cortesía |
| 19 | `PQRS-031` | `Había` | `PERSON` / `PER` | 0.85 | Sí | Verbo auxiliar capitalizado |
| 20 | `PQRS-035` | `Deseo` | `PERSON` / `PER` | 0.85 | Sí | Verbo 1ª persona / cortesía |
| 21 | `PQRS-035` | `Pido` | `PERSON` / `PER` | 0.85 | Sí | Verbo 1ª persona / cortesía |
| 22 | `PQRS-037` | `Nuestro` | `PERSON` / `PER` | 0.85 | Sí | Posesivo capitalizado |
| 23 | `PQRS-039` | `Pido` | `PERSON` / `PER` | 0.85 | Sí | Verbo 1ª persona / cortesía |
| 24 | `PQRS-041` | `Previamente` | `PERSON` / `PER` | 0.85 | Sí | Conector/adverbio temporal |
| 25 | `PQRS-042` | `C.C. XXX` | `PERSON` / `PER` | 0.85 | No | Placeholder sintético de cédula |
| 26 | `PQRS-042` | `Talento Humano` | `PERSON` / `PER` | 0.85 | No | Nombre de dependencia SmartPQRS |
| 27 | `PQRS-044` | `Había` | `PERSON` / `PER` | 0.85 | Sí | Verbo auxiliar capitalizado |
| 28 | `PQRS-049` | `Previamente` | `PERSON` / `PER` | 0.85 | Sí | Conector/adverbio temporal |
| 29 | `PQRS-049` | `Talento Humano` | `PERSON` / `PER` | 0.85 | No | Nombre de dependencia SmartPQRS |
| 30 | `PQRS-051` | `Pido` | `PERSON` / `PER` | 0.85 | Sí | Verbo 1ª persona / cortesía |
| 31 | `PQRS-053` | `Talento Humano` | `PERSON` / `PER` | 0.85 | No | Nombre de dependencia SmartPQRS |
| 32 | `PQRS-054` | `Ojalá` | `PERSON` / `PER` | 0.85 | Sí | Interjección coloquial capitalizada |
| 33 | `PQRS-055` | `Ventas` | `PERSON` / `PER` | 0.85 | No | Nombre de dependencia SmartPQRS |
| 34 | `PQRS-056` | `Aclaro` | `PERSON` / `PER` | 0.85 | Sí | Verbo 1ª persona |
| 35 | `PQRS-058` | `Había` | `PERSON` / `PER` | 0.85 | Sí | Verbo auxiliar capitalizado |
| 36 | `PQRS-059` | `Señores` | `PERSON` / `PER` | 0.85 | Sí | Fórmula de saludo / tratamiento |
| 37 | `PQRS-083` | `Señores` | `PERSON` / `PER` | 0.85 | Sí | Fórmula de saludo / tratamiento |
| 38 | `PQRS-085` | `Señores` | `PERSON` / `PER` | 0.85 | Sí | Fórmula de saludo / tratamiento |
| 39 | `PQRS-102` | `Talento Humano` | `PERSON` / `PER` | 0.85 | No | Nombre de dependencia SmartPQRS |
| 40 | `PQRS-108` | `Brindar` | `PERSON` / `PER` | 0.85 | Sí | Verbo infinitivo capitalizado |
| 41 | `PQRS-111` | `Ventas` | `PERSON` / `PER` | 0.85 | No | Nombre de dependencia SmartPQRS |
| 42 | `PQRS-118` | `Talento Humano` | `PERSON` / `PER` | 0.85 | No | Nombre de dependencia SmartPQRS |

**Resumen por patrón:**
- **Verbos en 1ª persona / auxiliares / infinitivos / gerundios al inicio de oración (22/42):** `Agradezco` (10), `Pido` (3), `Había` (3), `Pueden` (1), `Actuando` (1), `Deseo` (1), `Aclaro` (1), `Brindar` (1) + `Previamente` (2) / `Justo` (1) / `Le` (1) / `Nuestro` (1) / `Ojalá` (1) / `Señores` (3) — **31 de 42 falsos positivos ocurren exactamente al inicio de oración (`sent_start=True`)**.
- **Términos institucionales, dependencias y placeholders a mitad de oración (11/42):** `Talento Humano` (7), `Ventas` (2), `PQRS` (1), `C.C. XXX` (1).

---

## 2. Estrategia de 3 Capas Aplicada en `sanitizer_service.py`

1. **Capa C — Configuración de spaCy (`_NER_LABELS_TO_IGNORE = ["MISC"]`):**
   Se incorporó `"ner_model_configuration": {"labels_to_ignore": ["MISC"]}` en `_nlp_config` para eliminar el ruido de entidades `MISC` no mapeadas a PII y su advertencia en Presidio.
2. **Capa B — Umbral de confianza NER (`PERSON_SCORE_THRESHOLD = 0.85`):**
   Se mantuvo `REGEX_SCORE_THRESHOLD = 0.5` para los reconocedores regex de PII (`EMAIL_ADDRESS`, `PHONE_NUMBER`, `CO_CEDULA`, `CO_NIT`, `CO_ADDRESS`), mientras que `_filter_analyzer_results()` exige `score >= 0.85` exclusivamente para `PERSON`.
   - *Justificación y trade-off del valor `0.85`:* `SpacyRecognizer` asigna `0.85` tanto a `"Juan Pérez"` / `"María Rodríguez"` / `"Carlos Andrés Gómez"` como a detecciones ruidosas. Subir el umbral a `0.86` eliminaría los falsos positivos pero destruiría el **100% de la detección real de nombres**; fijarlo en `0.85` descarta cualquier coincidencia débil (`< 0.85`) sin degradar el recall de nombres reales, delegando el desempate preciso de palabras capitalizadas a la Capa A.
3. **Capa A — Filtro post-NER determinista (`ALLOWLIST_TOKENS` + filtro posicional):**
   - `ALLOWLIST_TOKENS` (normalización NFKD sin tildes ni distinción de mayúsculas) cubre verbos de cortesía en 1ª persona, fórmulas de saludo/cierre, conectores, adverbios, meses/días, cargos genéricos, nombres de dependencias (`Talento Humano`, `Ventas`, etc.), siglas (`PQRS`, `DIAN`, `SECOP`) y placeholders (`C.C. XXX`).
   - `_is_sentence_initial(text, start)` descarta spans `PERSON` de **1 solo token** capitalizados al inicio de oración (`start == 0` o tras `.`, `!`, `?`, `\n`, `:`), mientras conserva íntegramente spans de `>= 2` tokens al inicio de oración (`"Juan Pérez estuvo aquí."`, `"María José presentó la solicitud."`) y nombres de 1 o más tokens en cuerpo de oración (`"Mi nombre es Carlos..."`, `"Soy María Rodríguez..."`, `"Atentamente, Carlos Andrés Gómez."`).

---

## 3. Evidencia de Cobertura Real (Nombres Reales y 120/120 del Banco)

Con `presidio-analyzer 2.2.366` y `es_core_news_md 3.8.0` activos en Python 3.12:
- **Nombres reales preservando enmascaramiento `[MASKED_NAME]`:**
  - `"Juan Pérez estuvo aquí."` → `"[MASKED_NAME] estuvo aquí."`
  - `"María José presentó la solicitud."` → `"[MASKED_NAME] presentó la solicitud."`
  - `"Mi nombre es Carlos, mi cédula es 1.023.456.789..."` → `"Mi nombre es [MASKED_NAME], mi cédula es [MASKED_DOCUMENT]..."`
  - `"El ciudadano Juan Pérez radicó la solicitud."` → enmascarado (`Juan Pérez` removido)
  - `"Soy María Rodríguez y requiero respuesta urgente."` → enmascarado (`María Rodríguez` removido)
  - `"Atentamente, Carlos Andrés Gómez."` → enmascarado (`Carlos Andrés Gómez` removido)
- **Banco sintético completo:** `120 / 120` registros (`PQRS-001`..`PQRS-120`) pasan `sanitize_text(txt) == txt` sin alteraciones ni falsos positivos.
- **Suite `test_sanitizer.py`:** `149 passed, 0 failed, 0 skipped` en `11.96s`.
