-- ============================================================================
-- Migración SQL explícita: HU-17 (auditoria_ia) y HU-18 (auditoria_cambios)
-- PostgreSQL 16 — Script idempotente sobre el esquema base SmartPQRS
-- ============================================================================

-- 1. HU-17: Permitir histórico múltiple de decisiones IA por PQRS
DROP INDEX IF EXISTS ix_ai_audits_ticket_id;
CREATE INDEX IF NOT EXISTS ix_ai_audits_ticket_id
    ON ai_audits (ticket_id);
CREATE INDEX IF NOT EXISTS ix_ai_audits_ticket_created
    ON ai_audits (ticket_id, created_at);

-- 2. HU-18: Trazabilidad de funcionario responsable en intervenciones humanas
ALTER TABLE change_audits
    ADD COLUMN IF NOT EXISTS funcionario_id UUID;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'fk_change_audits_funcionario_id'
    ) THEN
        ALTER TABLE change_audits
            ADD CONSTRAINT fk_change_audits_funcionario_id
            FOREIGN KEY (funcionario_id)
            REFERENCES funcionarios (id)
            ON DELETE SET NULL;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS ix_change_audits_funcionario_id
    ON change_audits (funcionario_id);
CREATE INDEX IF NOT EXISTS ix_change_audits_ticket_created
    ON change_audits (ticket_id, created_at);

-- 3. Vistas canónicas de auditoría (contrato español HU-17 / HU-18)
CREATE OR REPLACE VIEW auditoria_ia AS
SELECT
    id,
    ticket_id AS id_pqrs,
    raw_response AS respuesta_cruda_json,
    decision_justification AS justificacion_decision,
    ai_model AS modelo,
    created_at AS "timestamp"
FROM ai_audits;

CREATE OR REPLACE VIEW auditoria_cambios AS
SELECT
    id,
    ticket_id AS id_pqrs,
    funcionario_id AS id_funcionario,
    modified_field AS campo_modificado,
    old_value AS valor_anterior,
    new_value AS valor_nuevo,
    created_at AS "timestamp"
FROM change_audits;
