# Frontend de demostración

Interfaz de demostración en Streamlit para validar el flujo del motor de
triaje: autenticación, dashboard, listado filtrable, detalle y auditoría de
PQRS, y alertas de vencimiento.

## Ejecución

Desde la raíz del proyecto:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r frontend\requirements.txt
streamlit run frontend\app.py
```

El backend debe estar disponible en `http://localhost:8000`. Para usar otra
dirección, configure `API_BASE_URL` antes de iniciar Streamlit:

```powershell
$env:API_BASE_URL = "http://localhost:8000"
streamlit run frontend\app.py
```

La aplicación no incluye credenciales. Inicie sesión con un funcionario creado
en el backend.

## Vistas disponibles

- **Dashboard:** total de PQRS, vencidas, próximas a vencer y distribución por
  fuente de clasificación.
- **Listado:** filtros por tipo, estado, prioridad y área, paginación y
  selección de un radicado para ver su detalle.
- **Alertas:** consulta de PQRS vencidas o próximas a vencer con filtro por
  nivel.
- **Crear PQRS:** formulario de ciudadano y solicitud, datos de ejemplo,
  clasificación automática y auditoría de la solicitud creada.

La URL del backend se configura con `API_BASE_URL`; su valor predeterminado es
`http://localhost:8000`.
