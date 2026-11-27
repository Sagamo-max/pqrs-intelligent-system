# Estimación e Impacto en Tokens — Comparativa Tripartita (`v1` / `v2-viejo` / `v2-nuevo`)

> **Metodología:** Conteo exacto de caracteres sobre los artefactos reales del repositorio (`classifier.py`, `classification.py`, `prompt_mejorado_v2.txt` y `banco_pqrs_sintetico.json`) aplicando la relación estándar **`1 token ≈ 4 caracteres` (`chars / 4`)**. Para el texto ciudadano variable se utiliza la longitud promedio real del banco regenerado (**`1.129.5` caracteres ≈ `282.4` tokens**).

---

## 1. Tabla Comparativa Tripartita de Tokens (`v1` vs `v2-viejo` vs `v2-nuevo`)

| Componente / Métrica | `v1` (Original en código) | `v2-viejo` (6 few-shots cortos ~148 chars) | `v2-nuevo` (6 few-shots realistas ~1.213 chars) | Alternativa evaluada `4 claros + 1 ambiguo` (5 few-shots) |
|---|---:|---:|---:|---:|
| Núcleo estático (Rol + Seguridad + Normativa + Reglas + Formato) | 471.0 *(111.5 prompt + ~359.5 schema)* | 779.0 *(3.116 chars)* | **779.0** *(3.116 chars, intacto)* | 779.0 *(3.116 chars)* |
| Bloque `[EJEMPLOS]` (caracteres / tokens) | 0 / **0.0** | 2.477 chars / **619.2** | 9.100 chars / **2.275.0** | 7.762 chars / **1.940.5** |
| **Total `SYSTEM_INSTRUCTIONS` estáticos** | **471.0** | **1.398.8** *(5.595 chars)* | **3.054.5** *(12.218 chars)* | **2.720.0** *(10.880 chars)* |
| ¿Supera umbral de *Prompt Caching* (`>= 1.024` tokens)? | **No** (`< 1.024`) | **Sí** (`1.37×` umbral) | **Sí** (`2.98×` umbral) | **Sí** (`2.66×` umbral) |
| Envoltura `USER_DATA_TEMPLATE` | 0.0 | 21.5 *(86 chars)* | **21.5** *(86 chars, intacta)* | 21.5 *(86 chars)* |
| Input dinámico ciudadano promedio (`1.129.5` chars) | 282.4 | 282.4 | **282.4** | 282.4 |
| **Total tokens de entrada nominales por PQRS** | **753.4** | **1.702.7** | **3.358.4** | **3.023.9** |
| Tokens de salida promedio (JSON) | ~90.0 *(sin tope, hasta 500 chars)* | ~52.0 *(minificado, `<=20` pal.)* | **~52.0** *(minificado, `<=20` pal.)* | ~52.0 *(minificado, `<=20` pal.)* |

---

## 2. Confirmación de Prompt Caching y Análisis de Costo con Hit-Rate Realista (60%–80%)

Con `3.054.5` tokens fijos e inmutables en `SYSTEM_INSTRUCTIONS`, **`v2-nuevo` activa automáticamente *Prompt Caching*** en los tres ecosistemas objetivo (todos con umbral mínimo de `1.024` tokens para este rango):
- **OpenAI GPT-4o:** entrada base `$2.50 / 1M`, lectura en caché `$1.25 / 1M` (**50% descuento**, sin recargo de escritura), salida `$10.00 / 1M`.
- **Anthropic Claude Sonnet:** entrada base `$3.00 / 1M`, escritura en caché (en *cache-miss*) `$3.75 / 1M`, lectura en caché (en *cache-hit*) `$0.30 / 1M` (**90% descuento**), salida `$15.00 / 1M`.

En operación real el *cache hit-rate* nunca es del 100% debido a expiración de TTL (5–10 minutos en valles nocturnos o baja concurrencia) y balanceo entre instancias. La siguiente tabla modela el **costo efectivo en USD por cada 1.000 solicitudes PQRS** (divide entre `1.000` para costo unitario por radicado):

| Versión del Prompt | GPT-4o *Cache-Miss* (0% hit) | GPT-4o **60% Hit** | GPT-4o **70% Hit** *(medio)* | GPT-4o **80% Hit** | Claude Sonnet *Sin caché* | Claude Sonnet **60% Hit** | Claude Sonnet **70% Hit** *(medio)* | Claude Sonnet **80% Hit** |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **`v1` (Original, sin caché `<1.024t`)** | \$2.78 | \$2.78 | \$2.78 | \$2.78 | \$3.61 | \$3.61 | \$3.61 | \$3.61 |
| **`v2-viejo` (6 cortos ~148 chars)** | \$4.78 | \$3.73 | \$3.55 | \$3.38 | \$5.89 | \$4.04 | \$3.56 | \$3.08 |
| **`v2-nuevo` (6 largos realistas)** | **\$8.92** | **\$6.63** | **\$6.24** | **\$5.86** | **\$10.86** | **\$6.82** | **\$5.77** | **\$4.72** |
| **Alternativa `4 claros + 1 ambiguo`** | \$8.08 | \$6.04 | \$5.70 | \$5.36 | \$9.85 | \$6.26 | \$5.32 | \$4.38 |

---

## 3. Veredicto y Recomendación Final

### Veredicto: **Mantener los 6 few-shots largos realistas en `prompt_mejorado_v2.txt`**

1. **Impacto económico acotado incluso en *cache-miss*:**
   - En el peor caso absoluto (*100% cache-miss*), `v2-nuevo` cuesta **\$0.00892 USD** por PQRS en GPT-4o (< 0.9 centavos de dólar).
   - En régimen realista de producción (**60%–80% de *cache hit***), el costo efectivo es de **\$0.00586 a \$0.00663 USD por PQRS** en GPT-4o (**\$6.24 por cada 1.000 PQRS** al 70% de *hit-rate*) y **\$0.00472 a \$0.00682 USD** en Claude Sonnet (**\$5.77 por cada 1.000 PQRS** al 70%). Para una entidad que reciba `10.000` PQRS/mes, el diferencial total frente a `v2-viejo` es de apenas **~\$22–\$27 USD/mes**, manteniéndose además muy por debajo de `4.096` tokens (`3.054.5` tokens estáticos).
2. **Por qué NO conviene recortar a `4 claros + 1 ambiguo` en operación estándar:**
   - Eliminar el sexto ejemplo apenas reduce **`334.5` tokens estáticos (`-10.9%`)**, lo que ahorra únicamente **\$0.54 USD por cada 1.000 PQRS** en GPT-4o (al 70% de *hit-rate*) o **\$0.84 por cada 1.000 PQRS** en *cache-miss*.
   - A cambio de ese ahorro marginal de \$0.00054 por radicado, se pierde **la mitad de los ejemplos ambiguos**, dejando sin ancla demostrativa una de las dos fronteras híbridas más propensas a error (`reclamo + petición` en `PQRS-027` o `queja + sugerencia` con regionalismos coloquiales en `PQRS-053`). Una sola intervención manual de reclasificación de un funcionario (HU-15 / HU-18) supera en costo laboral el ahorro de miles de tokens cacheados.
3. **Condición de contingencia documentada:**
   - Únicamente si el sistema se despliega en una instancia de muy bajo volumen (`< 1 radicado cada 10 minutos`, donde el *cache hit-rate* cae por debajo del 20%) o sobre un modelo local con contexto restringido (`<= 4.096` tokens), se recomienda retirar un ejemplo ambiguo pasando al esquema `4 + 1` (`2.720` tokens estáticos) sin acortar ni mutilar el texto de los registros restantes.
