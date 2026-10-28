from datetime import date

import holidays_co_full

from app.models.ticket import TicketType


SLA_DAYS: dict[TicketType, int] = {
    TicketType.PETITION: 15,
    TicketType.CLAIM: 15,
    TicketType.COMPLAINT: 15,
    TicketType.SUGGESTION: 15,
    TicketType.INFORMATION_REQUEST: 10,
}

DEFAULT_SLA_DAYS = 15


def calculate_due_date(filing_date: date, ticket_type: TicketType) -> date | None:
    """
    Calcula la fecha de vencimiento en días hábiles colombianos.

    Salvaguarda legal: si el tipo es CONSULTATION (30 días), retorna None
    para forzar validación humana.
    """
    if ticket_type == TicketType.CONSULTATION:
        return None

    days = SLA_DAYS.get(ticket_type, DEFAULT_SLA_DAYS)
    return holidays_co_full.add_business_days(filing_date, days)