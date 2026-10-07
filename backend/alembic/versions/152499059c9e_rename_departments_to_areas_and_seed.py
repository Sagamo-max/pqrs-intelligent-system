"""rename_departments_to_areas_and_seed

Revision ID: 152499059c9e
Revises: 05607d0df446
Create Date: 2026-10-07 16:21:24.994483

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '152499059c9e'
down_revision: Union[str, Sequence[str], None] = '05607d0df446'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1) Renombrar tabla
    op.rename_table("departments", "areas")

    # 2) Renombrar índices y constraint UNIQUE
    op.execute("ALTER INDEX ix_departments_id RENAME TO ix_areas_id")
    op.execute("ALTER INDEX ix_departments_code RENAME TO ix_areas_code")
    op.execute("ALTER TABLE areas RENAME CONSTRAINT departments_name_key TO areas_name_key")

    # 3) Ampliar code de VARCHAR(20) a VARCHAR(50)
    op.alter_column(
        "areas",
        "code",
        existing_type=sa.String(20),
        type_=sa.String(50),
        existing_nullable=False,
    )

    # 4) Nuevas columnas
    op.add_column("areas", sa.Column("description", sa.Text(), nullable=True))
    op.add_column(
        "areas",
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.false()),
    )

    # 5) Renombrar FK, columna e índice en tickets
    op.execute(
        "ALTER TABLE tickets RENAME CONSTRAINT tickets_department_id_fkey TO tickets_area_id_fkey"
    )
    op.alter_column("tickets", "department_id", new_column_name="area_id")
    op.execute("ALTER INDEX ix_tickets_department_id RENAME TO ix_tickets_area_id")

    # 6) Renombrar y ampliar columna en ai_audits
    op.alter_column(
        "ai_audits",
        "suggested_department_code",
        new_column_name="suggested_area_code",
        existing_type=sa.String(20),
        type_=sa.String(50),
        existing_nullable=False,
    )

    # 7) Seed del catálogo (idempotente por code)
    op.execute(
        """
        INSERT INTO areas (id, code, name, manager_email, is_default, is_active)
        VALUES
            (gen_random_uuid(), 'ATENCION_USUARIO', 'Atención al Usuario',      'atencion.usuario@empresa.com', TRUE,  TRUE),
            (gen_random_uuid(), 'FACTURACION',      'Facturación',               'facturacion@empresa.com',      FALSE, TRUE),
            (gen_random_uuid(), 'CARTERA',          'Cartera y Cobranza',        'cartera@empresa.com',          FALSE, TRUE),
            (gen_random_uuid(), 'VENTAS',           'Ventas',                    'ventas@empresa.com',           FALSE, TRUE),
            (gen_random_uuid(), 'SOPORTE_TECNICO',  'Soporte Técnico',           'soporte@empresa.com',          FALSE, TRUE),
            (gen_random_uuid(), 'TI',               'Tecnología e Informática',  'ti@empresa.com',               FALSE, TRUE),
            (gen_random_uuid(), 'LOGISTICA',        'Logística y Despachos',     'logistica@empresa.com',        FALSE, TRUE),
            (gen_random_uuid(), 'TALENTO_HUMANO',   'Talento Humano',            'rrhh@empresa.com',             FALSE, TRUE),
            (gen_random_uuid(), 'ADMINISTRACION',   'Administración y Finanzas', 'administracion@empresa.com',   FALSE, TRUE),
            (gen_random_uuid(), 'JURIDICA',         'Jurídica',                  'juridica@empresa.com',         FALSE, TRUE)
        ON CONFLICT (code) DO NOTHING
        """
    )

    # 8) Un único default permitido
    op.execute(
        """
        CREATE UNIQUE INDEX uq_areas_single_default
        ON areas (is_default)
        WHERE is_default = TRUE
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP INDEX IF EXISTS uq_areas_single_default")

    op.alter_column(
        "ai_audits",
        "suggested_area_code",
        new_column_name="suggested_department_code",
        existing_type=sa.String(50),
        type_=sa.String(20),
        existing_nullable=False,
    )

    op.execute("ALTER INDEX ix_tickets_area_id RENAME TO ix_tickets_department_id")
    op.alter_column("tickets", "area_id", new_column_name="department_id")
    op.execute(
        "ALTER TABLE tickets RENAME CONSTRAINT tickets_area_id_fkey TO tickets_department_id_fkey"
    )

    op.drop_column("areas", "is_default")
    op.drop_column("areas", "description")

    op.alter_column(
        "areas",
        "code",
        existing_type=sa.String(50),
        type_=sa.String(20),
        existing_nullable=False,
    )

    op.execute("ALTER INDEX ix_areas_code RENAME TO ix_departments_code")
    op.execute("ALTER INDEX ix_areas_id RENAME TO ix_departments_id")
    op.execute("ALTER TABLE areas RENAME CONSTRAINT areas_name_key TO departments_name_key")

    op.execute(
        """
        DELETE FROM areas WHERE code IN (
            'ATENCION_USUARIO','FACTURACION','CARTERA','VENTAS','SOPORTE_TECNICO',
            'TI','LOGISTICA','TALENTO_HUMANO','ADMINISTRACION','JURIDICA'
        )
        """
    )

    op.rename_table("areas", "departments")