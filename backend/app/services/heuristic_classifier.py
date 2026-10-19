import re
import unicodedata

from app.schemas.classification import AreaCode



KEYWORD_MAP: dict[AreaCode, list[str]] = {
    AreaCode.FACTURACION: [
        "factura", "facturacion", "nit", "iva", "recibo", "comprobante",
        "nota credito", "nota debito", "cobro",
    ],
    AreaCode.CARTERA: [
        "cartera", "cobranza", "deuda", "mora", "pago pendiente",
        "acuerdo de pago", "refinanciacion", "extracto",
    ],
    AreaCode.SOPORTE_TECNICO: [
        "error", "no funciona", "falla", "fallo", "bug", "se cae",
        "no responde", "soporte", "problema tecnico", "no carga",
    ],
    AreaCode.TI: [
        "app", "aplicacion", "sistema", "plataforma", "software",
        "login", "contrasena", "usuario bloqueado", "servidor",
    ],
    AreaCode.VENTAS: [
        "comprar", "cotizacion", "precio", "producto", "plan",
        "suscripcion", "asesor comercial", "nueva compra",
    ],
    AreaCode.LOGISTICA: [
        "envio", "entrega", "despacho", "paquete", "direccion",
        "transportadora", "rastreo", "guia",
    ],
    AreaCode.TALENTO_HUMANO: [
        "empleado", "nomina", "contrato laboral", "vacaciones",
        "talento humano", "rrhh", "certificado laboral",
    ],
    AreaCode.ADMINISTRACION: [
        "presupuesto", "contabilidad", "pago a proveedor",
        "orden de compra", "finanzas",
    ],
    AreaCode.JURIDICA: [
        "demanda", "legal", "abogado", "tutela",
        "derecho de peticion", "juridico",
    ],
}


def _normalize(text: str) -> str:
    """Lowercase + strip accents so 'facturación' matches 'facturacion'."""
    decomposed = unicodedata.normalize("NFKD", text)
    without_accents = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return without_accents.lower()


def heuristic_classify(text: str) -> AreaCode | None:
    """
    Return the area whose keyword set matches the most in the text.
    Returns None if no match, or if there is a tie between two or more areas
    with the same hit count (ambiguous case → fallback will handle it).
    """
    if not text:
        return None

    normalized = _normalize(text)
    
    hits: dict[AreaCode, int] = {}
    for area, keywords in KEYWORD_MAP.items():
        count = 0
        for kw in keywords:
            kw_norm = _normalize(kw)
            # Escape the keyword to avoid regex injection and use \b boundaries
            pattern = r"\b" + re.escape(kw_norm) + r"\b"
            if re.search(pattern, normalized):
                count += 1
        if count > 0:
            hits[area] = count

    if not hits:
        return None

    max_hits = max(hits.values())
    winners = [area for area, count in hits.items() if count == max_hits]

    if len(winners) == 1:
        return winners[0]

    return None