from datetime import date

import pytest

from app.models.ticket import TicketType
from app.services.sla import calculate_due_date


FILING_DATE = date(2026, 7, 6)


@pytest.mark.unit
def test_petition_15_business_days():
    due = calculate_due_date(FILING_DATE, TicketType.PETITION)

    assert due == date(2026, 7, 29)
    assert due > FILING_DATE
    assert due.weekday() < 5


@pytest.mark.unit
def test_information_request_10_business_days():
    due = calculate_due_date(FILING_DATE, TicketType.INFORMATION_REQUEST)

    assert due == date(2026, 7, 22)
    assert due > FILING_DATE
    assert due.weekday() < 5


@pytest.mark.unit
def test_consultation_returns_none():
    assert calculate_due_date(FILING_DATE, TicketType.CONSULTATION) is None


@pytest.mark.unit
def test_skips_weekends():
    friday = date(2026, 7, 10)

    due = calculate_due_date(friday, TicketType.PETITION)

    assert due > friday
    assert due.weekday() < 5


@pytest.mark.unit
def test_skips_holidays():
    due = calculate_due_date(FILING_DATE, TicketType.INFORMATION_REQUEST)

    assert due != date(2026, 7, 20)
    assert due > FILING_DATE
    assert due.weekday() < 5


@pytest.mark.unit
@pytest.mark.parametrize(
    "ticket_type",
    [
        TicketType.PETITION,
        TicketType.COMPLAINT,
        TicketType.CLAIM,
        TicketType.SUGGESTION,
        TicketType.INFORMATION_REQUEST,
    ],
)
def test_all_types_return_valid_date(ticket_type):
    due = calculate_due_date(FILING_DATE, ticket_type)

    assert due is not None
    assert due > FILING_DATE
    assert due.weekday() < 5


@pytest.mark.unit
@pytest.mark.parametrize(
    "ticket_type",
    [TicketType.CLAIM, TicketType.COMPLAINT, TicketType.SUGGESTION],
)
def test_claim_complaint_suggestion_use_general_15d(ticket_type):
    due = calculate_due_date(FILING_DATE, ticket_type)

    assert due == calculate_due_date(FILING_DATE, TicketType.PETITION)
