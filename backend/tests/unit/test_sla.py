import pytest
from datetime import date
from app.services.sla import calculate_due_date
from app.models.ticket import TicketType

@pytest.mark.unit
def test_calculate_due_date():
    due = calculate_due_date()
    assert due > date.today()
    diff = due - date.today()
    assert diff.days == 15  # # TODO: refactor needed for testability - Current implementation is fixed 15 days
    
@pytest.mark.unit
@pytest.mark.parametrize("ticket_type", [TicketType.PETITION, TicketType.COMPLAINT, TicketType.CLAIM, TicketType.SUGGESTION])
def test_calculate_due_date_types(ticket_type):
    due = calculate_due_date(ticket_type)
    assert (due - date.today()).days == 15

