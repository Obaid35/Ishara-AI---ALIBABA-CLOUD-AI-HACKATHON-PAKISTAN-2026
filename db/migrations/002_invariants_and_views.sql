-- Ishara AI — content-safety invariants and reporting views
-- Implements docs/DATA_MODEL.md "Invariants" and "Views".
-- These encode the project's safety rules in the one place that cannot be
-- forgotten under deadline pressure.

BEGIN;

-- ================================================================ helpers

-- The canonical audio staleness hash (I3). If this does not match
-- patient_messages.audio_source_checksum, the WAV was generated from
-- different text and must not be played.
CREATE OR REPLACE FUNCTION message_text_checksum(p_urdu text, p_kokoro text)
RETURNS text LANGUAGE sql IMMUTABLE AS $$
    SELECT md5(coalesce(p_urdu, '') || '||' || coalesce(p_kokoro, ''));
$$;

-- ================================================================ I1
-- A patient_message may be enabled only if EVERY sign in its concept
-- sequence is reliable + enabled.

CREATE OR REPLACE FUNCTION enforce_message_concepts_reliable()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    blocking text;
BEGIN
    IF NOT NEW.is_enabled THEN
        RETURN NEW;
    END IF;

    SELECT string_agg(s.code, ', ' ORDER BY mc.position)
      INTO blocking
      FROM message_concepts mc
      JOIN signs s ON s.id = mc.sign_id
     WHERE mc.message_id = NEW.id
       AND (s.reliability_status <> 'reliable' OR NOT s.is_enabled);

    IF blocking IS NOT NULL THEN
        RAISE EXCEPTION
            'I1: message "%" cannot be enabled — these signs are not Reliable + Enabled: %',
            NEW.code, blocking
            USING ERRCODE = 'check_violation';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM message_concepts WHERE message_id = NEW.id) THEN
        RAISE EXCEPTION 'I1: message "%" cannot be enabled — it has no concept sequence', NEW.code
            USING ERRCODE = 'check_violation';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_message_enable_guard
    BEFORE INSERT OR UPDATE ON patient_messages
    FOR EACH ROW EXECUTE FUNCTION enforce_message_concepts_reliable();

-- I1 cascade: demoting a sign automatically disables every message that
-- depended on it. Discovering the dependency by watching a demo step fail
-- is the failure mode this prevents.
CREATE OR REPLACE FUNCTION cascade_disable_dependent_messages()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF NEW.reliability_status = 'reliable' AND NEW.is_enabled THEN
        RETURN NEW;
    END IF;

    UPDATE patient_messages pm
       SET is_enabled = false,
           updated_at = now()
     WHERE pm.is_enabled
       AND EXISTS (
           SELECT 1 FROM message_concepts mc
            WHERE mc.message_id = pm.id AND mc.sign_id = NEW.id
       );

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_sign_demotion_cascade
    AFTER UPDATE OF reliability_status, is_enabled ON signs
    FOR EACH ROW EXECUTE FUNCTION cascade_disable_dependent_messages();

-- ================================================================ I2
-- A doctor_phrase may be enabled only if PSL-verified AND its video has
-- demo-playback permission.

CREATE OR REPLACE FUNCTION enforce_phrase_verified_and_permitted()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    permitted boolean;
BEGIN
    IF NOT NEW.is_enabled THEN
        RETURN NEW;
    END IF;

    IF NEW.verification_status <> 'psl_verified' THEN
        RAISE EXCEPTION 'I2: phrase "%" cannot be enabled — PSL is not verified', NEW.code
            USING ERRCODE = 'check_violation';
    END IF;

    IF NEW.psl_asset_id IS NULL THEN
        RAISE EXCEPTION 'I2: phrase "%" cannot be enabled — no PSL video attached', NEW.code
            USING ERRCODE = 'check_violation';
    END IF;

    SELECT ar.permitted_demo_playback INTO permitted
      FROM asset_rights ar WHERE ar.asset_id = NEW.psl_asset_id;

    IF permitted IS DISTINCT FROM true THEN
        RAISE EXCEPTION
            'I2: phrase "%" cannot be enabled — its PSL video has no demo-playback permission', NEW.code
            USING ERRCODE = 'check_violation';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_phrase_enable_guard
    BEFORE INSERT OR UPDATE ON doctor_phrases
    FOR EACH ROW EXECUTE FUNCTION enforce_phrase_verified_and_permitted();

-- ================================================================ I4
-- Per-sign margin overrides may only be STRICTER than the active config.
-- A sign that passes only with a loosened threshold is Weak and is removed.

CREATE OR REPLACE FUNCTION enforce_stricter_override_only()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    active_margin numeric;
BEGIN
    IF NEW.delta_margin_override IS NULL THEN
        RETURN NEW;
    END IF;

    SELECT delta_margin INTO active_margin
      FROM recognition_config WHERE is_active LIMIT 1;

    IF active_margin IS NOT NULL AND NEW.delta_margin_override < active_margin THEN
        RAISE EXCEPTION
            'I4: sign "%" override % is looser than the active margin % — stricter only',
            NEW.code, NEW.delta_margin_override, active_margin
            USING ERRCODE = 'check_violation';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_sign_override_guard
    BEFORE INSERT OR UPDATE ON signs
    FOR EACH ROW EXECUTE FUNCTION enforce_stricter_override_only();

-- ================================================================ I6
-- A sign_reference may be active only if its source asset permits development use.

CREATE OR REPLACE FUNCTION enforce_reference_dev_permission()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    permitted boolean;
BEGIN
    IF NOT NEW.is_active OR NEW.asset_id IS NULL THEN
        RETURN NEW;
    END IF;

    SELECT ar.permitted_development INTO permitted
      FROM asset_rights ar WHERE ar.asset_id = NEW.asset_id;

    IF permitted IS DISTINCT FROM true THEN
        RAISE EXCEPTION
            'I6: reference cannot be active — its source asset has no development permission'
            USING ERRCODE = 'check_violation';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_reference_rights_guard
    BEFORE INSERT OR UPDATE ON sign_references
    FOR EACH ROW EXECUTE FUNCTION enforce_reference_dev_permission();

-- ================================================================ views

-- The only sign count that may be quoted publicly.
CREATE VIEW v_production_vocabulary AS
SELECT s.*
  FROM signs s
 WHERE s.reliability_status = 'reliable'
   AND s.is_enabled;

-- Messages satisfying I1 and I3 (audio present and not stale).
CREATE VIEW v_demoable_messages AS
SELECT pm.id,
       pm.code,
       pm.urdu_text,
       pm.english_text,
       pm.priority,
       pm.is_demo_critical,
       a.path AS audio_path,
       (pm.audio_asset_id IS NOT NULL
        AND pm.audio_source_checksum
            = message_text_checksum(pm.urdu_text, pm.kokoro_input)) AS audio_ok,
       (SELECT string_agg(s.code, ' + ' ORDER BY mc.position)
          FROM message_concepts mc JOIN signs s ON s.id = mc.sign_id
         WHERE mc.message_id = pm.id) AS concept_sequence
  FROM patient_messages pm
  LEFT JOIN assets a ON a.id = pm.audio_asset_id
 WHERE pm.is_enabled;

CREATE VIEW v_demoable_doctor_phrases AS
SELECT dp.id,
       dp.code,
       dp.urdu_text,
       dp.english_text,
       dp.priority,
       dp.is_demo_critical,
       dp.sort_order,
       dp.stt_aliases,
       c.code AS category_code,
       c.name_en AS category_name_en,
       c.name_ur AS category_name_ur,
       c.sort_order AS category_sort_order,
       a.path AS video_path
  FROM doctor_phrases dp
  LEFT JOIN doctor_phrase_categories c ON c.id = dp.category_id
  LEFT JOIN assets a ON a.id = dp.psl_asset_id
 WHERE dp.is_enabled;

-- Assets referenced by enabled content whose rights are not settled.
-- Must be empty before the demo.
CREATE VIEW v_permission_gaps AS
SELECT a.id AS asset_id,
       a.kind,
       a.path,
       ar.permission_status,
       ar.source_name,
       'doctor_phrase: ' || dp.code AS used_by
  FROM doctor_phrases dp
  JOIN assets a ON a.id = dp.psl_asset_id
  LEFT JOIN asset_rights ar ON ar.asset_id = a.id
 WHERE dp.is_enabled
   AND (ar.asset_id IS NULL OR ar.permission_status IN ('unknown', 'requested'))
UNION ALL
SELECT a.id, a.kind, a.path, ar.permission_status, ar.source_name,
       'sign_reference: ' || s.code
  FROM sign_references sr
  JOIN signs s ON s.id = sr.sign_id
  JOIN assets a ON a.id = sr.asset_id
  LEFT JOIN asset_rights ar ON ar.asset_id = a.id
 WHERE sr.is_active
   AND (ar.asset_id IS NULL OR ar.permission_status IN ('unknown', 'requested'));

-- The query the team runs each morning instead of guessing.
CREATE VIEW v_demo_readiness AS
SELECT 'sign' AS item_type,
       s.code AS code,
       CASE
           WHEN s.reliability_status <> 'reliable' THEN 'not reliable (' || s.reliability_status || ')'
           WHEN NOT s.is_enabled THEN 'not enabled'
       END AS blocker
  FROM signs s
 WHERE s.is_demo_critical
   AND (s.reliability_status <> 'reliable' OR NOT s.is_enabled)
UNION ALL
SELECT 'message',
       pm.code,
       CASE
           WHEN NOT pm.is_enabled THEN 'not enabled'
           WHEN pm.audio_asset_id IS NULL THEN 'no audio generated'
           WHEN pm.audio_source_checksum IS DISTINCT FROM
                message_text_checksum(pm.urdu_text, pm.kokoro_input) THEN 'audio is stale'
       END
  FROM patient_messages pm
 WHERE pm.is_demo_critical
   AND (NOT pm.is_enabled
        OR pm.audio_asset_id IS NULL
        OR pm.audio_source_checksum IS DISTINCT FROM
           message_text_checksum(pm.urdu_text, pm.kokoro_input))
UNION ALL
SELECT 'doctor_phrase',
       dp.code,
       CASE
           WHEN dp.verification_status <> 'psl_verified' THEN 'PSL not verified'
           WHEN dp.psl_asset_id IS NULL THEN 'no PSL video'
           WHEN NOT dp.is_enabled THEN 'not enabled'
       END
  FROM doctor_phrases dp
 WHERE dp.is_demo_critical
   AND (dp.verification_status <> 'psl_verified'
        OR dp.psl_asset_id IS NULL
        OR NOT dp.is_enabled);

-- Compatibility views over the single assets table.
CREATE VIEW psl_assets AS SELECT * FROM assets WHERE kind = 'psl_video';
CREATE VIEW audio_assets AS SELECT * FROM assets WHERE kind = 'audio_wav';

COMMIT;
