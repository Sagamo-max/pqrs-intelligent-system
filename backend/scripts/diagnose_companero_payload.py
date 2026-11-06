"""
Diagnóstico: muestra el JSON exacto que se envía al compañero.
Uso: docker compose exec api python -m scripts.diagnose_companero_payload
"""
import json
import sys

from app.core.database import SessionLocal
from app.models.ticket import Ticket
from app.services.companero_client import _build_payload


def main() -> int:
    with SessionLocal() as db:
        ticket = db.query(Ticket).order_by(Ticket.created_at.desc()).first()
        if not ticket:
            print("ERROR: No hay tickets en la BD")
            return 1

        print("=" * 60)
        print(f"Ticket: {ticket.tracking_number}")
        print(f"Claimant: {ticket.claimant}")
        print("=" * 60)

        payload = _build_payload(ticket)
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        print("=" * 60)

        print("\nDiagnóstico del claimant:")
        if ticket.claimant:
            print(f"  - id: {ticket.claimant.id}")
            print(f"  - full_name: {getattr(ticket.claimant, 'full_name', 'N/A')}")
            print(f"  - first_name: {getattr(ticket.claimant, 'first_name', 'N/A')}")
            print(f"  - last_name: {getattr(ticket.claimant, 'last_name', 'N/A')}")
            print(f"  - email: {getattr(ticket.claimant, 'email', 'N/A')}")
            print(f"  - phone: {getattr(ticket.claimant, 'phone', 'N/A')}")
        else:
            print("  - claimant is None")
        return 0


if __name__ == "__main__":
    sys.exit(main())
