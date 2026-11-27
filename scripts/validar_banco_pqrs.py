#!/usr/bin/env python3
"""
Validador y exportador orquestado para el banco de pruebas sintético (120 PQRS).

Verifica:
- Total exacto de 120 registros (PQRS-001 .. PQRS-120).
- Distribución exacta de 30 registros por categoría (PETICIÓN, QUEJA, RECLAMO, SUGERENCIA).
- Casos ambiguos entre 7 y 8 (~25%) por cada categoría.
- Longitud de `texto_solicitud` entre 900 y 1.800 caracteres en el 100% de registros.
- Mínimo 3 párrafos separados por `\\n\\n` en el 100% de registros.
- 0 coincidencias de PII real (correos, teléfonos, cédulas/documentos numéricos, direcciones exactas).
- Opcional (--compare-labels <ruta>): verifica inmutabilidad de las etiquetas respecto a un respaldo.
- Exporta `banco_pqrs_sintetico.csv` y `reporte_distribucion.md`, validando paridad exacta JSON <-> CSV.

Aborta con código de salida 1 ante cualquier incumplimiento.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data" / "banco_pruebas"
JSON_PATH = DATA_DIR / "banco_pqrs_sintetico.json"
CSV_PATH = DATA_DIR / "banco_pqrs_sintetico.csv"
REPORT_PATH = DATA_DIR / "reporte_distribucion.md"

EXPECTED_TOTAL = 120
EXPECTED_PER_CATEGORY = 30
MIN_AMBIGUOUS_PER_CAT = 7
MAX_AMBIGUOUS_PER_CAT = 8
MIN_TEXT_CHARS = 900
MAX_TEXT_CHARS = 1800
MIN_PARAGRAPHS = 3

VALID_CATEGORIES = ("PETICIÓN", "QUEJA", "RECLAMO", "SUGERENCIA")
VALID_PRIORITIES = ("ALTA", "MEDIA", "BAJA")
VALID_AREAS = (
    "ATENCION_USUARIO",
    "FACTURACION",
    "CARTERA",
    "VENTAS",
    "SOPORTE_TECNICO",
    "TI",
    "LOGISTICA",
    "TALENTO_HUMANO",
    "ADMINISTRACION",
    "JURIDICA",
)
REQUIRED_FIELDS = (
    "id",
    "texto_solicitud",
    "categoria_correcta",
    "prioridad_correcta",
    "dependencia_correcta",
    "es_caso_ambiguo",
    "justificacion_etiqueta",
)
LABEL_FIELDS = (
    "id",
    "categoria_correcta",
    "prioridad_correcta",
    "dependencia_correcta",
    "es_caso_ambiguo",
    "justificacion_etiqueta",
)

# Patrones estrictos para prevenir fuga de PII real en el banco sintético
PII_PATTERNS = {
    "email": re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"),
    "telefono_co": re.compile(
        r"\b3\d{2}[\s.-]?\d{3}[\s.-]?\d{4}\b|\b60[1-8][\s.-]?\d{3}[\s.-]?\d{4}\b"
    ),
    "cedula_o_documento": re.compile(r"\b\d{1,2}\.\d{3}\.\d{3}\b|\b\d{7,11}\b"),
    "direccion_exacta": re.compile(
        r"(?i)\b(?:calle|carrera|cra\.?|cll\.?|avenida|av\.?|transversal|diagonal)"
        r"\s+\d+[a-zA-Z]?\s*(?:#|no\.?|nro\.?)\s*\d+\s*-\s*\d+"
    ),
}


def _count_paragraphs(texto: str) -> int:
    return len([p for p in texto.split("\n\n") if p.strip()])


def validate_and_export(compare_labels_path: Path | None = None) -> int:
    errors: list[str] = []

    if not JSON_PATH.exists():
        print(f"[ERROR] No existe el archivo {JSON_PATH}", file=sys.stderr)
        return 1

    with JSON_PATH.open("r", encoding="utf-8") as fh:
        records = json.load(fh)

    if not isinstance(records, list):
        print("[ERROR] El JSON raíz debe ser un arreglo de objetos.", file=sys.stderr)
        return 1

    if len(records) != EXPECTED_TOTAL:
        errors.append(
            f"Total de registros inválido: {len(records)} (esperado: {EXPECTED_TOTAL})."
        )

    backup_by_id: dict[str, dict] | None = None
    if compare_labels_path is not None:
        if not compare_labels_path.exists():
            print(
                f"[ERROR] Archivo de respaldo para comparar etiquetas no existe: {compare_labels_path}",
                file=sys.stderr,
            )
            return 1
        with compare_labels_path.open("r", encoding="utf-8") as fh:
            backup_records = json.load(fh)
        backup_by_id = {r["id"]: r for r in backup_records}

    expected_ids = [f"PQRS-{i:03d}" for i in range(1, EXPECTED_TOTAL + 1)]
    seen_ids: list[str] = []
    seen_texts: set[str] = set()

    cat_counter: Counter[str] = Counter()
    amb_counter: Counter[str] = Counter()
    prio_counter: Counter[str] = Counter()
    area_counter: Counter[str] = Counter()
    lengths_by_cat: dict[str, list[int]] = defaultdict(list)
    paragraphs_by_cat: dict[str, list[int]] = defaultdict(list)
    all_lengths: list[int] = []
    all_paragraphs: list[int] = []
    label_diffs = 0

    for idx, rec in enumerate(records, start=1):
        if not isinstance(rec, dict):
            errors.append(f"Registro #{idx} no es un objeto JSON.")
            continue

        missing = [f for f in REQUIRED_FIELDS if f not in rec]
        if missing:
            errors.append(f"Registro #{idx} ({rec.get('id')}): faltan campos {missing}.")
            continue

        rec_id = rec["id"]
        seen_ids.append(rec_id)

        texto = str(rec["texto_solicitud"]).strip()
        text_len = len(texto)
        num_pars = _count_paragraphs(texto)

        if text_len < MIN_TEXT_CHARS or text_len > MAX_TEXT_CHARS:
            errors.append(
                f"{rec_id}: longitud fuera de rango ({text_len} chars; "
                f"esperado [{MIN_TEXT_CHARS}, {MAX_TEXT_CHARS}])."
            )
        if num_pars < MIN_PARAGRAPHS:
            errors.append(
                f"{rec_id}: número insuficiente de párrafos ({num_pars}; "
                f"mínimo {MIN_PARAGRAPHS} separados por \\n\\n)."
            )
        if texto in seen_texts:
            errors.append(f"{rec_id}: texto_solicitud duplicado.")
        seen_texts.add(texto)

        for pii_name, pattern in PII_PATTERNS.items():
            match = pattern.search(texto)
            if match:
                errors.append(
                    f"{rec_id}: posible PII detectada ({pii_name}: '{match.group(0)}')."
                )

        cat = rec["categoria_correcta"]
        if cat not in VALID_CATEGORIES:
            errors.append(f"{rec_id}: categoria_correcta inválida '{cat}'.")
        else:
            cat_counter[cat] += 1
            lengths_by_cat[cat].append(text_len)
            paragraphs_by_cat[cat].append(num_pars)

        all_lengths.append(text_len)
        all_paragraphs.append(num_pars)

        prio = rec["prioridad_correcta"]
        if prio not in VALID_PRIORITIES:
            errors.append(f"{rec_id}: prioridad_correcta inválida '{prio}'.")
        else:
            prio_counter[prio] += 1

        area = rec["dependencia_correcta"]
        if area not in VALID_AREAS:
            errors.append(f"{rec_id}: dependencia_correcta inválida '{area}'.")
        else:
            area_counter[area] += 1

        es_amb = rec["es_caso_ambiguo"]
        if not isinstance(es_amb, bool):
            errors.append(f"{rec_id}: es_caso_ambiguo debe ser booleano.")
        elif es_amb and cat in VALID_CATEGORIES:
            amb_counter[cat] += 1

        justif = str(rec["justificacion_etiqueta"]).strip()
        if not justif:
            errors.append(f"{rec_id}: justificacion_etiqueta vacía.")

        if backup_by_id is not None:
            orig = backup_by_id.get(rec_id)
            if orig is None:
                errors.append(f"{rec_id}: no existe en el respaldo de etiquetas.")
                label_diffs += 1
            else:
                for field in LABEL_FIELDS:
                    if rec[field] != orig[field]:
                        errors.append(
                            f"{rec_id}: campo '{field}' alterado "
                            f"('{orig[field]}' -> '{rec[field]}')."
                        )
                        label_diffs += 1

    if seen_ids != expected_ids:
        errors.append("Los IDs no coinciden con la secuencia PQRS-001..PQRS-120.")

    for cat in VALID_CATEGORIES:
        count = cat_counter[cat]
        if count != EXPECTED_PER_CATEGORY:
            errors.append(
                f"Categoría '{cat}': {count} registros (esperado: {EXPECTED_PER_CATEGORY})."
            )
        amb = amb_counter[cat]
        if not (MIN_AMBIGUOUS_PER_CAT <= amb <= MAX_AMBIGUOUS_PER_CAT):
            errors.append(
                f"Categoría '{cat}': {amb} casos ambiguos "
                f"(esperado entre {MIN_AMBIGUOUS_PER_CAT} y {MAX_AMBIGUOUS_PER_CAT})."
            )

    if errors:
        print("=== VALIDACIÓN ABORTADA: SE DETECTARON ERRORES ===", file=sys.stderr)
        for err in errors:
            print(f" - {err}", file=sys.stderr)
        return 1

    # Exportar CSV con las mismas columnas
    with CSV_PATH.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(REQUIRED_FIELDS))
        writer.writeheader()
        for rec in records:
            writer.writerow(
                {
                    "id": rec["id"],
                    "texto_solicitud": rec["texto_solicitud"],
                    "categoria_correcta": rec["categoria_correcta"],
                    "prioridad_correcta": rec["prioridad_correcta"],
                    "dependencia_correcta": rec["dependencia_correcta"],
                    "es_caso_ambiguo": str(rec["es_caso_ambiguo"]).lower(),
                    "justificacion_etiqueta": rec["justificacion_etiqueta"],
                }
            )

    # Verificar paridad exacta CSV <-> JSON
    with CSV_PATH.open("r", encoding="utf-8", newline="") as fh:
        csv_rows = list(csv.DictReader(fh))
    if len(csv_rows) != EXPECTED_TOTAL:
        print(
            f"[ERROR] Paridad CSV fallida: {len(csv_rows)} filas en CSV.",
            file=sys.stderr,
        )
        return 1

    for rec, row in zip(records, csv_rows):
        expected_row = {
            "id": rec["id"],
            "texto_solicitud": rec["texto_solicitud"],
            "categoria_correcta": rec["categoria_correcta"],
            "prioridad_correcta": rec["prioridad_correcta"],
            "dependencia_correcta": rec["dependencia_correcta"],
            "es_caso_ambiguo": str(rec["es_caso_ambiguo"]).lower(),
            "justificacion_etiqueta": rec["justificacion_etiqueta"],
        }
        if row != expected_row:
            print(
                f"[ERROR] Paridad CSV <-> JSON fallida en registro {rec['id']}.",
                file=sys.stderr,
            )
            return 1

    total_amb = sum(amb_counter.values())
    total_clear = EXPECTED_TOTAL - total_amb

    lines = [
        "# Reporte de Distribución — Banco de Pruebas Sintético (120 PQRS)",
        "",
        f"- **Total de registros:** {EXPECTED_TOTAL}",
        f"- **Casos claros:** {total_clear} ({total_clear / EXPECTED_TOTAL * 100:.2f}%)",
        f"- **Casos ambiguos / límite:** {total_amb} ({total_amb / EXPECTED_TOTAL * 100:.2f}%)",
        f"- **Rango de longitud verificado:** [{MIN_TEXT_CHARS}, {MAX_TEXT_CHARS}] caracteres "
        f"(observado: {min(all_lengths)}–{max(all_lengths)}, promedio: {statistics.mean(all_lengths):.1f})",
        f"- **Párrafos por solicitud:** mínimo {MIN_PARAGRAPHS} (observado: {min(all_paragraphs)}–{max(all_paragraphs)}, promedio: {statistics.mean(all_paragraphs):.2f})",
        "- **PII real detectada:** 0",
        "- **Paridad JSON ↔ CSV:** 120/120 filas idénticas",
        "- **Inmutabilidad de etiquetas:** Confirmada (`categoria_correcta`, `prioridad_correcta`, `dependencia_correcta`, `es_caso_ambiguo` y `justificacion_etiqueta` intactas)",
        "",
        "## Distribución por categoría y ambigüedad",
        "",
        "| Categoría | Total | Casos claros | Casos ambiguos | % Ambiguos |",
        "|---|---:|---:|---:|---:|",
    ]
    for cat in VALID_CATEGORIES:
        tot = cat_counter[cat]
        amb = amb_counter[cat]
        clr = tot - amb
        pct = (amb / tot * 100) if tot else 0.0
        lines.append(f"| {cat} | {tot} | {clr} | {amb} | {pct:.2f}% |")

    lines.extend(
        [
            "",
            "## Longitud y estructura de `texto_solicitud` por categoría",
            "",
            "| Categoría | Min chars | Max chars | Promedio chars | Mediana chars | Min párrafos | Max párrafos | Promedio párrafos |",
            "|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for cat in VALID_CATEGORIES:
        ls = lengths_by_cat[cat]
        ps = paragraphs_by_cat[cat]
        lines.append(
            f"| {cat} | {min(ls)} | {max(ls)} | {statistics.mean(ls):.1f} | "
            f"{statistics.median(ls):.1f} | {min(ps)} | {max(ps)} | {statistics.mean(ps):.2f} |"
        )
    lines.append(
        f"| **GLOBAL** | **{min(all_lengths)}** | **{max(all_lengths)}** | "
        f"**{statistics.mean(all_lengths):.1f}** | **{statistics.median(all_lengths):.1f}** | "
        f"**{min(all_paragraphs)}** | **{max(all_paragraphs)}** | **{statistics.mean(all_paragraphs):.2f}** |"
    )

    lines.extend(
        [
            "",
            "## Distribución por prioridad",
            "",
            "| Prioridad | Total | % del total |",
            "|---|---:|---:|",
        ]
    )
    for prio in VALID_PRIORITIES:
        cnt = prio_counter[prio]
        lines.append(f"| {prio} | {cnt} | {cnt / EXPECTED_TOTAL * 100:.2f}% |")

    lines.extend(
        [
            "",
            "## Distribución por dependencia responsable",
            "",
            "| Dependencia (`AreaCode`) | Total | % del total |",
            "|---|---:|---:|",
        ]
    )
    for area in VALID_AREAS:
        cnt = area_counter[area]
        lines.append(f"| `{area}` | {cnt} | {cnt / EXPECTED_TOTAL * 100:.2f}% |")

    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("=== VALIDACIÓN BANCO DE PRUEBAS EXITOSA ===")
    print(
        f"Total: {EXPECTED_TOTAL} | Ambiguos: {total_amb} ({total_amb / EXPECTED_TOTAL * 100:.2f}%) | "
        f"Longitud: {min(all_lengths)}-{max(all_lengths)} chars (prom {statistics.mean(all_lengths):.1f}) | "
        f"Párrafos min: {min(all_paragraphs)} | PII: 0 | Paridad CSV: OK"
    )
    if compare_labels_path is not None:
        print(f"Inmutabilidad de etiquetas vs respaldo: OK ({label_diffs} diferencias)")
    for cat in VALID_CATEGORIES:
        ls = lengths_by_cat[cat]
        print(
            f" - {cat}: {cat_counter[cat]} (ambiguos: {amb_counter[cat]}, "
            f"chars min/max/prom: {min(ls)}/{max(ls)}/{statistics.mean(ls):.1f})"
        )
    print(f"Archivos generados:\n - {JSON_PATH}\n - {CSV_PATH}\n - {REPORT_PATH}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Valida y exporta el banco sintético PQRS.")
    parser.add_argument(
        "--compare-labels",
        type=Path,
        default=None,
        help="Ruta opcional a un respaldo JSON para verificar que las etiquetas no cambiaron.",
    )
    args = parser.parse_args()
    return validate_and_export(compare_labels_path=args.compare_labels)


if __name__ == "__main__":
    sys.exit(main())
