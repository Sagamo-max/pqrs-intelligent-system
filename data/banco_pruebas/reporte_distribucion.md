# Reporte de Distribución — Banco de Pruebas Sintético (120 PQRS)

- **Total de registros:** 120
- **Casos claros:** 89 (74.17%)
- **Casos ambiguos / límite:** 31 (25.83%)
- **Rango de longitud verificado:** [900, 1800] caracteres (observado: 979–1532, promedio: 1129.5)
- **Párrafos por solicitud:** mínimo 3 (observado: 3–3, promedio: 3.00)
- **PII real detectada:** 0
- **Paridad JSON ↔ CSV:** 120/120 filas idénticas
- **Inmutabilidad de etiquetas:** Confirmada (`categoria_correcta`, `prioridad_correcta`, `dependencia_correcta`, `es_caso_ambiguo` y `justificacion_etiqueta` intactas)

## Distribución por categoría y ambigüedad

| Categoría | Total | Casos claros | Casos ambiguos | % Ambiguos |
|---|---:|---:|---:|---:|
| PETICIÓN | 30 | 22 | 8 | 26.67% |
| QUEJA | 30 | 22 | 8 | 26.67% |
| RECLAMO | 30 | 23 | 7 | 23.33% |
| SUGERENCIA | 30 | 22 | 8 | 26.67% |

## Longitud y estructura de `texto_solicitud` por categoría

| Categoría | Min chars | Max chars | Promedio chars | Mediana chars | Min párrafos | Max párrafos | Promedio párrafos |
|---|---:|---:|---:|---:|---:|---:|---:|
| PETICIÓN | 979 | 1506 | 1135.6 | 1091.0 | 3 | 3 | 3.00 |
| QUEJA | 990 | 1467 | 1125.9 | 1095.5 | 3 | 3 | 3.00 |
| RECLAMO | 992 | 1512 | 1139.8 | 1055.0 | 3 | 3 | 3.00 |
| SUGERENCIA | 1006 | 1532 | 1116.6 | 1079.5 | 3 | 3 | 3.00 |
| **GLOBAL** | **979** | **1532** | **1129.5** | **1084.5** | **3** | **3** | **3.00** |

## Distribución por prioridad

| Prioridad | Total | % del total |
|---|---:|---:|
| ALTA | 27 | 22.50% |
| MEDIA | 50 | 41.67% |
| BAJA | 43 | 35.83% |

## Distribución por dependencia responsable

| Dependencia (`AreaCode`) | Total | % del total |
|---|---:|---:|
| `ATENCION_USUARIO` | 15 | 12.50% |
| `FACTURACION` | 13 | 10.83% |
| `CARTERA` | 13 | 10.83% |
| `VENTAS` | 11 | 9.17% |
| `SOPORTE_TECNICO` | 13 | 10.83% |
| `TI` | 10 | 8.33% |
| `LOGISTICA` | 14 | 11.67% |
| `TALENTO_HUMANO` | 11 | 9.17% |
| `ADMINISTRACION` | 10 | 8.33% |
| `JURIDICA` | 10 | 8.33% |
