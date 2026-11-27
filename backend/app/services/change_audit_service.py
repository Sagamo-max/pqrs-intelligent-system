from sqlalchemy.orm import Session

from app.models.audit import ChangeAudit


def create_change_audit(
    db: Session,
    ticket_id,
    responsible_user: str,
    event_type: str,
    modified_field: str,
    old_value: str | None,
    new_value: str,
    change_reason: str | None = None,
    funcionario_id=None,
) -> ChangeAudit:
    audit = ChangeAudit(
        ticket_id=ticket_id,
        funcionario_id=funcionario_id,
        responsible_user=responsible_user,
        event_type=event_type,
        modified_field=modified_field,
        old_value=old_value,
        new_value=new_value,
        change_reason=change_reason or "",
    )
    db.add(audit)
    db.flush()
    return audit