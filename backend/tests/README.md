# Pruebas del Backend

Este directorio contiene la suite completa de pruebas unitarias y de integración para el sistema inteligente de PQRS, garantizando que cumple con las reglas del negocio, la Ley 1755 y el manejo de datos personales.

## Requisitos
Las pruebas requieren una base de datos PostgreSQL real (por uso de tipos UUID y JSONB) configurada en la variable de entorno `TEST_DATABASE_URL`. También necesitan el modelo de lenguaje de spaCy cargado.

## Ejecución local

1. Activa tu entorno virtual e instala dependencias:
   ```powershell
   pip install pytest pytest-cov pytest-mock httpx
   python -m spacy download es_core_news_sm
   ```

2. Configura tu variable de base de datos de pruebas (asegúrate de que esté vacía o aislada):
   ```powershell
   $env:TEST_DATABASE_URL="postgresql://usuario:password@localhost:5432/ticket_db_test"
   ```

3. Ejecuta todas las pruebas:
   ```powershell
   pytest
   ```

4. Ejecuta solo pruebas unitarias:
   ```powershell
   pytest tests/unit/
   ```

5. Ejecuta con reporte de cobertura:
   ```powershell
   pytest --cov=app --cov-report=term-missing
   ```

**Nota:** Las pruebas aíslan la red; las interacciones con la API de OpenAI están simuladas (mocked) para no incurrir en costos.

