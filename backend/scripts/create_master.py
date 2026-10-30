"""Bootstrap script to create the first MASTER user.

Usage (inside Docker):
    docker compose exec -it api python -m scripts.create_master

Usage (local with venv, against Docker DB):
    $env:DATABASE_URL = "postgresql+psycopg://postgres:admin@localhost:5432/ticket_db"
    python scripts/create_master.py

The script is idempotent: if the username already exists, it aborts safely.
"""

import getpass
import sys
from pathlib import Path

# Ensure ``app`` is importable from any working directory.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select

# Import all models before importing a specific model so SQLAlchemy can resolve
# relationships such as Ticket -> AIAuditAttempt.
import app.models  # noqa: F401
import app.models.audit_attempt  # noqa: F401

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.funcionario import Funcionario, FuncionarioRole


def main() -> int:
    print("=== Create MASTER user ===")

    username = input("Username del MASTER: ").strip()
    if not username:
        print("ERROR: el username no puede estar vacío.")
        return 1

    password = getpass.getpass("Password (mínimo 8 caracteres): ")
    if len(password) < 8:
        print("ERROR: la contraseña debe tener al menos 8 caracteres.")
        return 1

    confirm = getpass.getpass("Confirm password: ")
    if password != confirm:
        print("ERROR: las contraseñas no coinciden.")
        return 1

    full_name = input("Nombre completo (opcional): ").strip() or None

    try:
        with SessionLocal() as db:
            existing = db.scalar(
                select(Funcionario).where(Funcionario.username == username)
            )
            if existing:
                print(f"ERROR: el username '{username}' ya existe.")
                return 1

            funcionario = Funcionario(
                username=username,
                hashed_password=hash_password(password),
                full_name=full_name,
                role=FuncionarioRole.MASTER,
                area_id=None,
                is_active=True,
            )
            db.add(funcionario)
            db.commit()
            db.refresh(funcionario)

            print(f"OK: MASTER '{username}' creado exitosamente.")
            print(f"    id: {funcionario.id}")
            print(f"    role: {funcionario.role.value}")
            return 0
    except Exception as exc:
        print(f"ERROR inesperado: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
