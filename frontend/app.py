import os
import re
from datetime import date, datetime
from typing import Any

import httpx
import pandas as pd
import streamlit as st


API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")
ORGANIZATION_SLUG = os.getenv("ORGANIZATION_SLUG", "demo")
TICKET_TYPES = [
    "Todos",
    "PETITION",
    "COMPLAINT",
    "CLAIM",
    "SUGGESTION",
    "INFORMATION_REQUEST",
]
TICKET_STATUSES = ["Todos", "RECEIVED", "IN_PROGRESS", "RESOLVED", "CLOSED"]
PRIORITIES = ["Todas", "HIGH", "MEDIUM", "LOW"]
DOCUMENT_TYPES = ["CC", "CE", "NIT", "PASSPORT", "TI"]
TYPE_LABELS = {
    "PETITION": "📋 PETITION",
    "COMPLAINT": "⚠️ COMPLAINT",
    "CLAIM": "🔴 CLAIM",
    "SUGGESTION": "💡 SUGGESTION",
    "INFORMATION_REQUEST": "❓ INFORMATION_REQUEST",
}
PRIORITY_LABELS = {"HIGH": "🔴 HIGH", "MEDIUM": "🟡 MEDIUM", "LOW": "🟢 LOW"}
EXAMPLE_PQRS = {
    "claimant_full_name": "María José Rodríguez",
    "claimant_document_type": "CC",
    "claimant_document_number": "1234567890",
    "claimant_email": "maria@example.com",
    "claimant_phone": "3001234567",
    "free_text": (
        "Necesito que me corrijan una factura con mi NIT nuevo. "
        "Mi cédula es 1.234.567 y mi correo es maria@example.com."
    ),
}


@st.cache_data(ttl=300)
def fetch_organization() -> dict[str, str] | None:
    """Fetch the active organization used by the public PQRS form."""
    try:
        response = httpx.get(
            _api_url("/api/v1/organizaciones/active"),
            params={"slug": ORGANIZATION_SLUG},
            timeout=5,
        )
        response.raise_for_status()
        data = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        st.error(f"No se pudo obtener la organización activa: {exc}")
        return None

    if not isinstance(data, dict) or not data.get("id"):
        st.error("El backend no devolvió una organización válida.")
        return None
    return data


def _api_url(path: str) -> str:
    return f"{API_BASE_URL}{path}"


def _headers() -> dict[str, str]:
    token = st.session_state.get("access_token")
    return {"Authorization": f"Bearer {token}"} if token else {}


def _clear_session() -> None:
    for key in (
        "access_token",
        "refresh_token",
        "user",
        "selected_ticket",
        "creation_result",
    ):
        st.session_state.pop(key, None)


def _logout() -> None:
    refresh_token = st.session_state.get("refresh_token")
    if refresh_token:
        try:
            httpx.post(
                _api_url("/api/auth/logout"),
                headers=_headers(),
                json={"refresh_token": refresh_token},
                timeout=10,
            )
        except httpx.RequestError:
            pass
    _clear_session()


def _get(path: str, **kwargs: Any) -> httpx.Response | None:
    try:
        response = httpx.get(
            _api_url(path),
            headers=_headers(),
            timeout=10,
            **kwargs,
        )
    except httpx.RequestError:
        st.error("No fue posible conectarse con el backend.")
        return None

    if response.status_code == 401:
        _clear_session()
        st.warning("Sesión expirada. Inicia sesión de nuevo.")
        st.rerun()
    if response.is_error:
        st.error("No fue posible obtener la información solicitada.")
        return None
    return response


def _json(response: httpx.Response, message: str) -> Any | None:
    try:
        return response.json()
    except (ValueError, TypeError):
        st.error(message)
        return None


def _format_date(value: Any) -> str:
    if not value:
        return "Sin fecha"
    return str(value)[:10]


def _format_datetime(value: Any) -> str:
    if not value:
        return "Sin fecha"
    return str(value).replace("T", " ")[:19]


def _date_value(value: Any) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def _datetime_value(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def _login_screen() -> None:
    st.markdown('<div class="main-header">PQRS Intelligent System</div>', unsafe_allow_html=True)
    st.write("Demostración del motor de clasificación y enrutamiento inteligente.")
    st.subheader("Iniciar sesión")

    with st.form("login_form"):
        username = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        submitted = st.form_submit_button("Iniciar sesión", type="primary", use_container_width=True)

    if not submitted:
        return

    try:
        response = httpx.post(
            _api_url("/api/auth/login"),
            json={"username": username, "password": password},
            timeout=10,
        )
    except httpx.RequestError:
        st.error("No fue posible conectarse con el backend.")
        return

    if response.is_error:
        st.error("Usuario o contraseña incorrectos.")
        return

    data = _json(response, "La respuesta de autenticación no es válida.")
    if not isinstance(data, dict) or not data.get("access_token"):
        st.error("No fue posible iniciar sesión.")
        return

    st.session_state.access_token = data["access_token"]
    st.session_state.refresh_token = data.get("refresh_token")
    st.rerun()


def _load_user() -> dict[str, Any] | None:
    if "user" not in st.session_state:
        response = _get("/api/auth/me")
        if response is None:
            return None
        data = _json(response, "La respuesta del usuario no es válida.")
        if not isinstance(data, dict):
            return None
        st.session_state.user = data
    return st.session_state.user


def _load_areas() -> list[dict[str, Any]]:
    response = _get("/api/v1/areas/")
    if response is None:
        return []
    data = _json(response, "No fue posible cargar las áreas.")
    return data if isinstance(data, list) else []


def _sidebar(user: dict[str, Any], areas: list[dict[str, Any]]) -> None:
    with st.sidebar:
        st.header("Sesión activa")
        st.write(user.get("full_name") or user.get("username", "Usuario"))
        st.caption(f"Rol: **{user.get('role', 'N/D')}**")
        st.divider()
        st.subheader("Filtros de PQRS")
        st.selectbox("Tipo", TICKET_TYPES, key="filter_ticket_type")
        st.selectbox("Estado", TICKET_STATUSES, key="filter_status")
        st.selectbox("Prioridad", PRIORITIES, key="filter_priority")
        area_options = {"Todas": None}
        area_options.update(
            {
                f"{area.get('name', 'Sin nombre')} ({area.get('code', '')})": area.get("id")
                for area in areas
            }
        )
        st.selectbox("Área", list(area_options), key="filter_area")
        st.divider()
        if st.button("Cerrar sesión", use_container_width=True):
            _logout()
            st.rerun()


def _ticket_params() -> dict[str, Any]:
    params: dict[str, Any] = {
        "limit": st.session_state.get("page_limit", 20),
        "offset": st.session_state.get("page_offset", 0),
    }
    values = (
        ("filter_ticket_type", "ticket_type", "Todos"),
        ("filter_status", "status", "Todos"),
        ("filter_priority", "priority", "Todas"),
    )
    for state_key, query_key, empty_value in values:
        value = st.session_state.get(state_key, empty_value)
        if value != empty_value:
            params[query_key] = value
    area_id = st.session_state.get("filter_area_id")
    if area_id:
        params["area_id"] = area_id
    return params


def _ticket_rows(tickets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "tracking_number": ticket.get("tracking_number", ""),
            "ticket_type": ticket.get("ticket_type", ""),
            "priority": ticket.get("priority", ""),
            "status": ticket.get("status", ""),
            "area": (ticket.get("area") or {}).get("name", "Sin asignar"),
            "due_date": _date_value(ticket.get("due_date")),
            "created_at": _datetime_value(ticket.get("created_at")),
        }
        for ticket in tickets
    ]


def _priority_style(row: pd.Series) -> list[str]:
    color = {"HIGH": "#ffc7ce", "MEDIUM": "#ffeb9c", "LOW": "#c6efce"}.get(
        row.get("priority", ""),
        "",
    )
    return [f"background-color: {color}" if column == "priority" else "" for column in row.index]


def _render_ticket_table(rows: list[dict[str, Any]]) -> None:
    dataframe = pd.DataFrame(rows)
    if dataframe.empty:
        st.info("No hay PQRS que coincidan con los filtros seleccionados.")
        return
    styled = dataframe.style.apply(_priority_style, axis=1)
    st.dataframe(
        styled,
        use_container_width=True,
        hide_index=True,
        column_config={
            "tracking_number": st.column_config.TextColumn("Radicado"),
            "ticket_type": st.column_config.TextColumn("Tipo"),
            "priority": st.column_config.TextColumn("Prioridad"),
            "status": st.column_config.TextColumn("Estado"),
            "area": st.column_config.TextColumn("Área"),
            "due_date": st.column_config.DateColumn("Vencimiento", format="YYYY-MM-DD"),
            "created_at": st.column_config.DatetimeColumn("Creada", format="YYYY-MM-DD HH:mm"),
        },
    )


def _load_ticket_list() -> tuple[list[dict[str, Any]], int]:
    response = _get("/api/v1/pqrs/", params=_ticket_params())
    if response is None:
        return [], 0
    payload = _json(response, "La respuesta de PQRS no es válida.")
    if isinstance(payload, dict):
        items = payload.get("items", [])
        return (items if isinstance(items, list) else [], int(payload.get("total", 0)))
    return (payload if isinstance(payload, list) else [], len(payload) if isinstance(payload, list) else 0)


def _render_ticket_detail(tracking_number: str) -> None:
    response = _get(f"/api/v1/pqrs/{tracking_number}/audit")
    if response is None:
        return
    audit = _json(response, "La respuesta de auditoría no es válida.")
    if not isinstance(audit, dict):
        return

    st.markdown("---")
    st.subheader(f"Detalle de PQRS: {tracking_number}")
    ticket_rows = st.session_state.get("ticket_rows_by_tracking", {})
    ticket = ticket_rows.get(tracking_number, {})
    details = st.columns(6)
    for column, label, key in zip(
        details,
        ("Radicado", "Estado", "Tipo", "Prioridad", "Vencimiento", "Creada"),
        ("tracking_number", "status", "ticket_type", "priority", "due_date", "created_at"),
    ):
        value = (
            _format_date(ticket.get(key))
            if key in {"due_date", "created_at"}
            else ticket.get(key, "N/D")
        )
        column.markdown(f"**{label}**  \n{value}")

    area = ticket.get("area_data") or {}
    area_columns = st.columns(2)
    area_columns[0].markdown(f"**Área asignada:** {area.get('name', 'Sin asignar')}")
    area_columns[1].markdown(f"**Email del manager:** {area.get('manager_email', 'No disponible')}")

    with st.expander("Texto original", expanded=True):
        st.text_area("Contenido original", audit.get("original_text", "No disponible"), height=160, disabled=True)
    with st.expander("Texto sanitizado"):
        st.text_area("Contenido sanitizado", audit.get("sanitized_text", "No disponible"), height=160, disabled=True)

    st.markdown("#### Clasificación de la IA")
    classification_columns = st.columns(4)
    classification_fields = (
        ("Tipo sugerido", audit.get("suggested_type", "N/D")),
        ("Prioridad sugerida", audit.get("suggested_priority", "N/D")),
        ("Área sugerida", audit.get("suggested_area_code", "N/D")),
        ("Fuente", audit.get("classification_source", audit.get("provider", "N/D"))),
    )
    for column, (label, value) in zip(classification_columns, classification_fields):
        column.markdown(f"**{label}**  \n{value}")
    st.info(audit.get("decision_justification", "No hay justificación disponible."))

    with st.expander("Metadata de clasificación"):
        st.json(
            {
                "tokens_used": audit.get("tokens_used"),
                "latency_ms": audit.get("latency_ms"),
                "confidence": audit.get("confidence"),
                "ai_model": audit.get("ai_model"),
                "created_at": audit.get("created_at"),
            }
        )

    if st.button("Ver auditoría completa", key=f"audit_{tracking_number}"):
        st.json(audit)


def _listing_page(areas: list[dict[str, Any]]) -> None:
    st.markdown('<div class="main-header">Listado de PQRS</div>', unsafe_allow_html=True)
    area_by_id = {area.get("id"): area for area in areas}
    st.session_state.filter_area_id = {
        label: area_id
        for label, area_id in {
            "Todas": None,
            **{
                f"{area.get('name', 'Sin nombre')} ({area.get('code', '')})": area.get("id")
                for area in areas
            },
        }.items()
    }.get(st.session_state.get("filter_area", "Todas"))

    pagination = st.columns(2)
    pagination[0].number_input("Resultados por página", min_value=1, max_value=100, value=20, step=1, key="page_limit")
    pagination[1].number_input("Desplazamiento", min_value=0, value=0, step=20, key="page_offset")
    tickets, total = _load_ticket_list()
    rows = _ticket_rows(tickets)
    for ticket, row in zip(tickets, rows):
        row["area_data"] = area_by_id.get((ticket.get("area") or {}).get("id"), ticket.get("area") or {})
    st.caption(f"Mostrando {len(rows)} resultados de un total de {total}.")
    _render_ticket_table([{key: value for key, value in row.items() if key != "area_data"} for row in rows])

    st.session_state.ticket_rows_by_tracking = {
        row["tracking_number"]: row for row in rows
    }
    choices = ["Selecciona un radicado"] + [row["tracking_number"] for row in rows]
    selected = st.selectbox("Selecciona una PQRS para ver el detalle", choices)
    if selected != "Selecciona un radicado" and st.button("Ver detalle", type="primary"):
        st.session_state.selected_ticket = selected
    if selected != "Selecciona un radicado" and st.session_state.get("selected_ticket") == selected:
        _render_ticket_detail(selected)


def _alerts_page() -> None:
    st.markdown('<div class="main-header">Alertas de vencimiento</div>', unsafe_allow_html=True)
    level = st.selectbox("Nivel de alerta", ["Todos", "OVERDUE", "DUE_SOON"], key="alert_level")
    params = {} if level == "Todos" else {"level": level}
    response = _get("/api/v1/pqrs/alerts", params=params)
    if response is None:
        return
    alerts = _json(response, "La respuesta de alertas no es válida.")
    if not isinstance(alerts, list):
        return
    rows = [
        {
            "tracking_number": item.get("tracking_number"),
            "status": item.get("status"),
            "due_date": _date_value(item.get("due_date")),
            "alert_level": item.get("alert_level"),
            "days_remaining": item.get("days_remaining"),
        }
        for item in alerts
    ]
    if rows:
        dataframe = pd.DataFrame(rows)
        st.dataframe(
            dataframe.style.apply(
                lambda row: [
                    "background-color: #ffc7ce" if row.get("alert_level") == "OVERDUE"
                    else "background-color: #ffeb9c" if row.get("alert_level") == "DUE_SOON"
                    else ""
                    for _ in row.index
                ],
                axis=1,
            ),
            use_container_width=True,
            hide_index=True,
            column_config={"due_date": st.column_config.DateColumn("Vencimiento", format="YYYY-MM-DD")},
        )
    else:
        st.success("No hay alertas para el filtro seleccionado.")


def _dashboard_page() -> None:
    st.markdown('<div class="main-header">Dashboard del motor de triaje</div>', unsafe_allow_html=True)
    total_response = _get("/api/v1/pqrs/", params={"limit": 1})
    overdue_response = _get("/api/v1/pqrs/alerts", params={"level": "OVERDUE"})
    due_soon_response = _get("/api/v1/pqrs/alerts", params={"level": "DUE_SOON"})
    stats_response = _get("/api/v1/pqrs/stats")
    if not all((total_response, overdue_response, due_soon_response, stats_response)):
        return

    total_data = _json(total_response, "No fue posible cargar el total de PQRS.")
    overdue = _json(overdue_response, "No fue posible cargar las PQRS vencidas.")
    due_soon = _json(due_soon_response, "No fue posible cargar las PQRS próximas a vencer.")
    stats = _json(stats_response, "No fue posible cargar las estadísticas.")
    if not isinstance(total_data, dict) or not isinstance(overdue, list) or not isinstance(due_soon, list) or not isinstance(stats, dict):
        return

    metrics = st.columns(3)
    metrics[0].metric("Total de PQRS", total_data.get("total", 0))
    metrics[1].metric("Vencidas", len(overdue), delta="Requieren atención", delta_color="inverse")
    metrics[2].metric("Próximas a vencer", len(due_soon), delta="En los próximos días", delta_color="off")

    source_counts = stats.get("all_time", {}).get("by_source", {})
    chart = pd.DataFrame(
        {"Clasificaciones": [source_counts.get(source, 0) for source in ("openai", "heuristic", "fallback")]},
        index=["OpenAI", "Heuristic", "Fallback"],
    )
    st.subheader("Distribución por fuente de clasificación")
    st.bar_chart(chart, color="#1f77b4")


def _show_creation_errors(response: httpx.Response) -> None:
    if response.status_code == 422:
        detail = _json(response, "La solicitud contiene datos inválidos.")
        if isinstance(detail, dict) and isinstance(detail.get("detail"), list):
            st.error("Corrige los siguientes campos:")
            for error in detail["detail"]:
                location = error.get("loc", [])
                field = ".".join(str(item) for item in location if item != "body")
                st.error(f"{field or 'Solicitud'}: {error.get('msg', 'Valor inválido')}")
        else:
            st.error("La solicitud contiene datos inválidos.")
    elif response.status_code >= 500:
        st.error("Error al crear la PQRS. Intenta de nuevo.")
    else:
        st.error("No fue posible crear la PQRS. Verifica los datos e intenta de nuevo.")


def _validate_creation_form(values: dict[str, str]) -> list[str]:
    errors = []
    if len(values["full_name"].strip()) < 3:
        errors.append("El nombre completo debe tener al menos 3 caracteres.")
    if len(values["document_number"].strip()) < 5:
        errors.append("El número de documento debe tener al menos 5 caracteres.")
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", values["email"].strip()):
        errors.append("Ingresa un correo electrónico válido.")
    if not re.fullmatch(r"\d{10}", values["phone"].strip()):
        errors.append("El teléfono debe contener exactamente 10 dígitos.")
    if len(values["free_text"].strip()) < 15:
        errors.append("El texto de la PQRS debe tener al menos 15 caracteres.")
    return errors


def _render_creation_result() -> None:
    result = st.session_state.get("creation_result")
    if not isinstance(result, dict):
        return

    tracking_number = result.get("tracking_number", "N/D")
    st.success(f"PQRS creada: {tracking_number}")
    st.subheader("Resultado de la clasificación automática")
    details = st.columns(6)
    ticket_fields = (
        ("Radicado", tracking_number),
        ("Estado", result.get("status", "N/D")),
        ("Tipo", TYPE_LABELS.get(result.get("ticket_type"), result.get("ticket_type", "N/D"))),
        ("Prioridad", PRIORITY_LABELS.get(result.get("priority"), result.get("priority", "N/D"))),
        ("Área", (result.get("area") or {}).get("name", "Sin asignar")),
        ("Vencimiento", _format_date(result.get("due_date"))),
    )
    for column, (label, value) in zip(details, ticket_fields):
        column.markdown(f"**{label}**  \n{value}")

    audit = result.get("audit") or {}
    source = audit.get("classification_source", audit.get("provider", "N/D"))
    source_color = {"openai": "🟢", "heuristic": "🟡", "fallback": "🔴"}.get(source, "⚪")
    st.markdown(f"**Fuente de clasificación:** {source_color} `{source}`")
    st.info(audit.get("decision_justification", "No hay justificación disponible."))
    with st.expander("Texto original"):
        st.text_area("Texto original de la solicitud", audit.get("original_text", "No disponible"), height=140, disabled=True)
    with st.expander("Texto sanitizado"):
        st.text_area("Texto sanitizado enviado al clasificador", audit.get("sanitized_text", "No disponible"), height=140, disabled=True)
    if st.button("Ver en el listado", key="view_created_ticket"):
        st.session_state.creation_result = None
        st.session_state.selected_ticket = tracking_number
        st.rerun()


def _creation_page() -> None:
    st.markdown('<div class="main-header">Crear PQRS</div>', unsafe_allow_html=True)
    st.write("Registra una solicitud y observa cómo el motor la clasifica y enruta automáticamente.")
    organization = fetch_organization()
    if organization is None:
        st.error("No se puede crear la PQRS sin una organización activa.")
        return
    st.caption(f"Organización: {organization.get('name', ORGANIZATION_SLUG)}")

    if st.button("Rellenar con datos de ejemplo", key="fill_example"):
        for key, value in EXAMPLE_PQRS.items():
            st.session_state[key] = value
        st.rerun()

    with st.form("create_pqrs_form"):
        st.markdown("#### A. Datos del ciudadano")
        claimant_columns = st.columns(2)
        full_name = claimant_columns[0].text_input(
            "Nombre completo *",
            key="claimant_full_name",
        )
        document_type = claimant_columns[1].selectbox(
            "Tipo de documento *",
            DOCUMENT_TYPES,
            key="claimant_document_type",
        )
        document_number = claimant_columns[0].text_input(
            "Número de documento *",
            key="claimant_document_number",
        )
        email = claimant_columns[1].text_input(
            "Correo electrónico *",
            key="claimant_email",
        )
        phone = claimant_columns[0].text_input(
            "Teléfono (10 dígitos) *",
            key="claimant_phone",
        )

        st.markdown("#### B. Texto de la PQRS")
        free_text = st.text_area(
            "Solicitud *",
            placeholder=(
                "Ej: Necesito que me corrijan una factura con mi NIT nuevo. "
                "Mi nombre es María José y mi cédula es 1.234.567."
            ),
            key="free_text",
            height=180,
        )
        st.caption(f"Caracteres: {len(free_text)}")
        submitted = st.form_submit_button("Enviar PQRS", type="primary", use_container_width=True)

    if submitted:
        values = {
            "full_name": full_name,
            "document_number": document_number,
            "email": email,
            "phone": phone,
            "free_text": free_text,
        }
        errors = _validate_creation_form(values)
        if errors:
            for error in errors:
                st.error(error)
            return

        payload = {
            "claimant": {
                "full_name": full_name.strip(),
                "document_type": document_type,
                "document_number": document_number.strip(),
                "email": email.strip(),
                "phone": phone.strip(),
            },
            "free_text": free_text.strip(),
            "organization_id": organization["id"],
        }
        try:
            response = httpx.post(
                _api_url("/api/v1/pqrs/"),
                headers=_headers(),
                json=payload,
                timeout=30,
            )
        except httpx.RequestError:
            st.error("No fue posible conectarse con el backend.")
            return

        if response.status_code == 401:
            _clear_session()
            st.warning("Sesión expirada. Inicia sesión de nuevo.")
            st.rerun()
        if response.is_error:
            _show_creation_errors(response)
            return

        ticket = _json(response, "La respuesta de creación no es válida.")
        if not isinstance(ticket, dict) or not ticket.get("tracking_number"):
            st.error("El backend no devolvió un ticket válido.")
            return

        audit_response = _get(f"/api/v1/pqrs/{ticket['tracking_number']}/audit")
        audit = _json(audit_response, "La PQRS fue creada, pero no se pudo cargar su auditoría.") if audit_response else {}
        ticket["audit"] = audit if isinstance(audit, dict) else {}
        st.session_state.creation_result = ticket
        st.rerun()

    _render_creation_result()


def _authenticated_app(user: dict[str, Any], areas: list[dict[str, Any]]) -> None:
    _sidebar(user, areas)
    dashboard_tab, listing_tab, alerts_tab, creation_tab = st.tabs(
        ["Dashboard", "Listado", "Alertas", "Crear PQRS"]
    )
    with dashboard_tab:
        _dashboard_page()
    with listing_tab:
        _listing_page(areas)
    with alerts_tab:
        _alerts_page()
    with creation_tab:
        _creation_page()


st.set_page_config(page_title="PQRS Intelligent System", page_icon="📋", layout="wide")
st.markdown(
    """
    <style>
        .main-header { font-size: 2rem; color: #1f77b4; font-weight: bold; margin-bottom: 1rem; }
        .stMetric { background-color: #f0f2f6; padding: 10px; border-radius: 10px; }
    </style>
    """,
    unsafe_allow_html=True,
)

if st.session_state.get("access_token"):
    current_user = _load_user()
    if current_user is not None:
        loaded_areas = _load_areas()
        _authenticated_app(current_user, loaded_areas)
else:
    _login_screen()
