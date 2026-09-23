from datetime import date, timedelta

def calculate_due_date(ticket_type: str = "PETITION") -> date:
    return date.today() + timedelta(days=15)