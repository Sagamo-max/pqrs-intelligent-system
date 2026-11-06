"""
Diagnóstico: muestra el texto original y sanitizado.
Uso: docker compose exec api python -m scripts.diagnose_sanitizer
"""
from app.services.sanitizer_service import sanitize_text


def main() -> None:
    test_texts = [
        "Mi nombre es Carlos Andrés Mendoza y mi correo es carlos@empresa.com.co",
        "Mi cédula es 1.023.456.789 y mi teléfono es 310 555 7788",
        "El NIT de mi empresa es 900.123.456-7",
        "Hola, soy María José Rodríguez",
    ]

    for text in test_texts:
        sanitized = sanitize_text(text)
        print("=" * 60)
        print(f"Original:  {text}")
        print(f"Sanitized: {sanitized}")
        print("=" * 60)


if __name__ == "__main__":
    main()
