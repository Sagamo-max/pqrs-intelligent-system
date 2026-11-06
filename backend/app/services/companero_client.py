import logging
import json
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.ticket import Ticket

logger = logging.getLogger(__name__)


def _build_payload(ticket: Ticket) -> dict[str, Any]:
    """Build the payload expected by the companion API."""
    claimant = ticket.claimant
    audit = ticket.ai_audit
    client_name = (
        f"{claimant.first_name} {claimant.last_name}".strip()
        if claimant
        else ""
    )

    payload = {
        "ticket_type": (
            ticket.ticket_type.value
            if hasattr(ticket.ticket_type, "value")
            else str(ticket.ticket_type)
        ),
        "priority": (
            ticket.priority.value
            if hasattr(ticket.priority, "value")
            else str(ticket.priority)
        ),
        "department_code": ticket.area.code if ticket.area else "ATENCION_USUARIO",
        "text": audit.sanitized_text if audit else "",
        "tracking_number": ticket.tracking_number,
        "external_reference": ticket.tracking_number,
        "client_name": client_name,
        "client_email": claimant.email if claimant else "",
        "due_date": ticket.due_date.isoformat() if ticket.due_date else None,
        "decision_justification": audit.decision_justification if audit else "",
    }
    logger.info(
        "Payload to companero API: %s",
        json.dumps(payload, indent=2, ensure_ascii=False),
    )
    return payload


def send_pqr_to_companero(db: Session, ticket: Ticket) -> bool:
    """Send a PQRS to the companion API without affecting ticket creation."""
    del db

    if not settings.COMPANERO_API_ENABLED:
        logger.debug("COMPANERO_API_ENABLED=False, skipping send")
        return False

    if not settings.COMPANERO_API_URL or not settings.COMPANERO_API_KEY:
        logger.warning(
            "Companero API credentials not configured, skipping send"
        )
        return False

    url = f"{settings.COMPANERO_API_URL.rstrip('/')}/api/v1/intake/pqr"
    logger.info(
        "Sending PQR %s to companero API. URL=%s, KEY_PRESENT=%s",
        ticket.tracking_number,
        url,
        bool(settings.COMPANERO_API_KEY),
    )
    payload = _build_payload(ticket)

    try:
        with httpx.Client(timeout=settings.COMPANERO_API_TIMEOUT_SECONDS) as client:
            response = client.post(
                url,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "X-API-Key": settings.COMPANERO_API_KEY,
                },
            )
            response.raise_for_status()
            logger.info(
                "PQR %s sent to companero API (status=%s)",
                ticket.tracking_number,
                response.status_code,
            )
            return True
    except httpx.HTTPStatusError as exc:
        logger.error(
            "Companero API returned error for %s: %s - %s",
            ticket.tracking_number,
            exc.response.status_code,
            exc.response.text[:500],
        )
    except httpx.RequestError as exc:
        logger.error(
            "Network error sending %s to companero API: %s",
            ticket.tracking_number,
            exc,
        )
    except Exception:
        logger.exception(
            "Unexpected error sending %s to companero API",
            ticket.tracking_number,
        )
    return False
