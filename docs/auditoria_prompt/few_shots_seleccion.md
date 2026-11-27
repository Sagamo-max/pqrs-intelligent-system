# Selección y Trazabilidad de Few-Shots Realistas — Prompt v2 (`few_shots_seleccion.md`)

## 1. Resumen de los 6 registros seleccionados (`banco_pqrs_sintetico.json` regenerado)

Todos los textos fueron extraídos **textualmente (carácter por carácter, 3 párrafos separados por `\n\n`)** del banco validado, priorizando el rango medio-alto de longitud (`1.029 – 1.428` caracteres; promedio `1.213.3` chars) y garantizando máxima diversidad de categorías, ambigüedad, tonos, canales, prioridades y dependencias:

| # | ID | Categoría | Prioridad | Dependencia (`AreaCode`) | `es_caso_ambiguo` | `confianza` | Chars | Perfil / Tono y Canal | Frontera / Criterio que enseña al modelo |
|---:|---|---|---|---|---|---:|---:|---|---|
| 1 | **`PQRS-014`** | `PETICIÓN` | `ALTA` | `JURIDICA` | `false` | `0.94` | 1.428 | Formal institucional / agente oficioso de paciente vulnerable (ventanilla + canal jurídico) | **Petición clara de prioridad ALTA:** solicitud documental amparada en fallo de tutela sin reproche previo; rompe el sesgo de asignar `BAJA` a toda petición. |
| 2 | **`PQRS-040`** | `QUEJA` | `MEDIA` | `TI` | `false` | `0.92` | 1.113 | Adulto mayor (correo electrónico + llamada a mesa de ayuda) | **Queja clara vs soporte técnico:** aunque ocurre usando la plataforma virtual, el objeto es denunciar la burla y el trato humillante del analista sin pedir reparación material. |
| 3 | **`PQRS-076`** | `RECLAMO` | `MEDIA` | `VENTAS` | `false` | `0.93` | 1.334 | Empresarial / gerencia comercial con NIT (correo corporativo + auditoría) | **Reclamo claro contractual:** incumplimiento de descuento por volumen durante tres periodos exigiendo nota de abono retroactiva y ajuste tarifario. |
| 4 | **`PQRS-093`** | `SUGERENCIA` | `BAJA` | `ADMINISTRACION` | `false` | `0.95` | 1.260 | Ciudadano común acompañante de persona con discapacidad visual (presencial) | **Sugerencia clara constructiva:** destaca explícitamente el buen trato recibido y propone instalar braille y audioguía en cajeros de radicación. |
| 5 | **`PQRS-027`** | `PETICIÓN` | `MEDIA` | `FACTURACION` | `true` | `0.66` | 1.116 | Ciudadano común con giros coloquiales (*"duda medio enredada"*, portal web + teléfono) | **Frontera híbrida `reclamo + petición`:** reporta un *"saldo raro"*, pero pospone explícitamente controvertir (*"antes de pelear o presentar cualquier reclamo formal"*) para pedir explicación concepto por concepto. |
| 6 | **`PQRS-053`** | `QUEJA` | `MEDIA` | `TALENTO_HUMANO` | `true` | `0.68` | 1.029 | Coloquial regional costeño (*"Qué rabia hombre"*, *"a las patadas"*, ventanilla en Barranquilla) | **Frontera híbrida `queja + sugerencia` + `coloquial difícil`:** cierra sugiriendo capacitar al personal, pero el núcleo dominante es reprochar el maltrato verbal y gestual del cajero. |

---

## 2. Cobertura alcanzada

- **Estratificación obligatoria (Tarea 1):** `4` casos claros (`1 PETICIÓN`, `1 QUEJA`, `1 RECLAMO`, `1 SUGERENCIA`) con `confianza >= 0.92` + `2` casos ambiguos con `es_ambiguo: true` y `confianza < 0.70` (`0.66` y `0.68`).
- **Fronteras críticas cubiertas:**
  1. `reclamo + petición` (`PQRS-027`).
  2. `queja + sugerencia` combinada con `coloquial difícil` y regionalismos (`PQRS-053`).
  3. Desambiguación transversal de áreas y prioridades: `6` dependencias distintas sin repetición (`JURIDICA`, `TI`, `VENTAS`, `ADMINISTRACION`, `FACTURACION`, `TALENTO_HUMANO`) y los `3` niveles de prioridad (`ALTA`, `MEDIA`, `BAJA`).
- **Variedad sociolingüística y de canal:** formal jurídico (`014`), adulto mayor en soporte digital (`040`), sociedad comercial B2B (`076`), accesibilidad ciudadana presencial (`093`), usuario residencial web/teléfono (`027`) y lenguaje coloquial espontáneo (`053`).

---

## 3. Diff frente a los IDs anteriores (`v2-viejo` → `v2-nuevo`)

En `v2-viejo`, los **6 ejemplos eran todos `es_caso_ambiguo=true`** (`PQRS-027`, `053`, `056`, `084`, `088`, `113`) y tenían ~148 caracteres (una sola oración). Para cumplir la estructura de Tarea 1 (**4 claros por categoría + 2 ambiguos realistas**), se conservaron los **2 IDs originales más representativos** y se reemplazaron los 4 restantes por anclas claras de 3 párrafos en el rango `1.100–1.500` caracteres:

| Slot | Antes (`v2-viejo`) | Estado | Ahora (`v2-nuevo`) | Motivo técnico del cambio / conservación |
|---:|---|---|---|---|
| 1 | `PQRS-027` *(PETICIÓN ambigua, 170 chars)* | **CONSERVADO** *(reubicado a Ejemplo 5)* | **`PQRS-027`** *(PETICIÓN ambigua, 1.116 chars)* | Sigue siendo el mejor caso frontera `reclamo + petición` y su texto regenerado (1.116 chars) cae exactamente en el rango objetivo `1.100–1.500`. |
| 2 | `PQRS-053` *(QUEJA ambigua, 168 chars)* | **CONSERVADO** *(reubicado a Ejemplo 6)* | **`PQRS-053`** *(QUEJA ambigua, 1.029 chars)* | Conserva trazabilidad directa y cubre simultáneamente dos fronteras exigidas: `queja + sugerencia` y `coloquial difícil` regional. |
| 3 | `PQRS-056` *(QUEJA ambigua, 151 chars)* | Reemplazado | **`PQRS-014`** *(PETICIÓN clara, 1.428 chars)* | Se requería 1 `PETICIÓN` clara (`es_caso_ambiguo=false`) de tono formal institucional y prioridad `ALTA`. |
| 4 | `PQRS-084` *(RECLAMO ambiguo, 170 chars)* | Reemplazado | **`PQRS-040`** *(QUEJA clara, 1.113 chars)* | Se requería 1 `QUEJA` clara (`es_caso_ambiguo=false`); además aporta la voz de **adulto mayor** y desambigua quejas de trato en `TI`. |
| 5 | `PQRS-088` *(RECLAMO ambiguo, 159 chars)* | Reemplazado | **`PQRS-076`** *(RECLAMO claro, 1.334 chars)* | Se requería 1 `RECLAMO` claro (`es_caso_ambiguo=false`); aporta perfil **empresarial (NIT)** y área `VENTAS`. |
| 6 | `PQRS-113` *(SUGERENCIA ambigua, 165 chars)* | Reemplazado | **`PQRS-093`** *(SUGERENCIA clara, 1.260 chars)* | Se requería 1 `SUGERENCIA` clara (`es_caso_ambiguo=false`); aporta canal presencial, prioridad `BAJA` y área `ADMINISTRACION`. |
