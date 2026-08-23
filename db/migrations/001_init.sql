-- Ishara AI — initial schema
-- Implements docs/DATA_MODEL.md
-- Rules: no patient identity, no stored consultations, no blobs in the database.

BEGIN;

CREATE EXTENSION IF NOT EXISTS citext;

-- ---------------------------------------------------------------- enums

CREATE TYPE verification_status AS ENUM ('draft', 'psl_verified', 'rejected');
CREATE TYPE reliability_status  AS ENUM ('candidate', 'experimenting', 'testing', 'reliable', 'weak', 'dropped');
CREATE TYPE priority_level      AS ENUM ('p0', 'p1', 'p2');
CREATE TYPE asset_kind          AS ENUM ('psl_video', 'audio_wav', 'reference_clip');
CREATE TYPE permission_status   AS ENUM ('unknown', 'requested', 'granted', 'denied', 'own_recording');
CREATE TYPE consent_purpose     AS ENUM ('development', 'internal_testing', 'demo_playback', 'public_release');
CREATE TYPE test_level          AS ENUM ('t1_source', 't2_live_team', 't3_second_person', 't4_unseen', 't5_room_variation');
CREATE TYPE trial_outcome       AS ENUM ('correct', 'wrong', 'unknown_ambiguous', 'unknown_no_match');

-- ---------------------------------------------------------------- reference data

CREATE TABLE roles (
    code        text PRIMARY KEY,
    name        text NOT NULL,
    description text NOT NULL DEFAULT ''
);

CREATE TABLE settings (
    key        text PRIMARY KEY,
    value      jsonb NOT NULL,
    updated_by uuid,
    updated_at timestamptz NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------- identity

CREATE TABLE users (
    id                   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    email                citext UNIQUE NOT NULL,
    username             citext UNIQUE,
    password_hash        text NOT NULL,
    full_name            text NOT NULL DEFAULT '',
    role_code            text NOT NULL REFERENCES roles(code),
    is_active            boolean NOT NULL DEFAULT true,
    must_change_password boolean NOT NULL DEFAULT true,
    last_login_at        timestamptz,
    created_by           uuid REFERENCES users(id),
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_users_role ON users(role_code);

CREATE TABLE auth_sessions (
    id                 uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id            uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    refresh_token_hash text NOT NULL,
    issued_at          timestamptz NOT NULL DEFAULT now(),
    expires_at         timestamptz NOT NULL,
    revoked_at         timestamptz,
    user_agent         text,
    ip                 text
);
CREATE INDEX idx_auth_sessions_user ON auth_sessions(user_id);
CREATE INDEX idx_auth_sessions_token ON auth_sessions(refresh_token_hash);

CREATE TABLE password_resets (
    id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id    uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash text NOT NULL,
    expires_at timestamptz NOT NULL,
    used_at    timestamptz,
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_password_resets_token ON password_resets(token_hash);

-- Append-only. Never updated, never deleted from the application.
CREATE TABLE audit_logs (
    id          bigserial PRIMARY KEY,
    user_id     uuid REFERENCES users(id),
    action      text NOT NULL,
    entity_type text NOT NULL,
    entity_id   text,
    before      jsonb,
    after       jsonb,
    ip          text,
    created_at  timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_audit_created ON audit_logs(created_at DESC);
CREATE INDEX idx_audit_entity ON audit_logs(entity_type, entity_id);

-- ---------------------------------------------------------------- assets and rights

CREATE TABLE assets (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    kind        asset_kind NOT NULL,
    path        text UNIQUE NOT NULL,
    checksum    text NOT NULL DEFAULT '',
    bytes       bigint NOT NULL DEFAULT 0,
    duration_ms integer,
    created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE asset_rights (
    asset_id                   uuid PRIMARY KEY REFERENCES assets(id) ON DELETE CASCADE,
    source_name                text NOT NULL DEFAULT '',
    source_url                 text,
    permission_status          permission_status NOT NULL DEFAULT 'unknown',
    permitted_development      boolean NOT NULL DEFAULT false,
    permitted_internal_testing boolean NOT NULL DEFAULT false,
    permitted_demo_playback    boolean NOT NULL DEFAULT false,
    permitted_public_release   boolean NOT NULL DEFAULT false,
    requested_on               date,
    responded_on               date,
    license_notes              text,
    evidence_ref               text
);

-- ---------------------------------------------------------------- participants and consent

CREATE TABLE test_participants (
    id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    participant_code text UNIQUE NOT NULL,
    is_unseen        boolean NOT NULL DEFAULT false,
    notes            text NOT NULL DEFAULT ''
);

CREATE TABLE consents (
    id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    participant_id uuid NOT NULL REFERENCES test_participants(id) ON DELETE CASCADE,
    purpose        consent_purpose NOT NULL,
    granted        boolean NOT NULL DEFAULT false,
    granted_on     date,
    evidence_ref   text,
    UNIQUE (participant_id, purpose)
);

-- ---------------------------------------------------------------- vocabulary

CREATE TABLE signs (
    id                     uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    code                   text UNIQUE NOT NULL,
    urdu_meaning           text NOT NULL DEFAULT '',
    english_meaning        text NOT NULL DEFAULT '',
    verification_status    verification_status NOT NULL DEFAULT 'draft',
    reliability_status     reliability_status NOT NULL DEFAULT 'candidate',
    is_enabled             boolean NOT NULL DEFAULT false,
    verified_by            text,
    verified_on            date,
    regional_variant_note  text,
    delta_margin_override  numeric,
    is_demo_critical       boolean NOT NULL DEFAULT false,
    notes                  text NOT NULL DEFAULT '',
    created_at             timestamptz NOT NULL DEFAULT now(),
    updated_at             timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_signs_enabled ON signs(is_enabled, reliability_status);

CREATE TABLE sign_variants (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    sign_id     uuid NOT NULL REFERENCES signs(id) ON DELETE CASCADE,
    label       text NOT NULL,
    region_note text,
    is_default  boolean NOT NULL DEFAULT false,
    is_enabled  boolean NOT NULL DEFAULT true
);

CREATE TABLE sign_references (
    id                 uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    sign_id            uuid NOT NULL REFERENCES signs(id) ON DELETE CASCADE,
    variant_id         uuid REFERENCES sign_variants(id) ON DELETE SET NULL,
    asset_id           uuid REFERENCES assets(id) ON DELETE SET NULL,
    landmark_path      text,
    landmark_checksum  text,
    extractor_version  text NOT NULL DEFAULT '',
    frame_count        integer,
    source_fps         numeric,
    participant_id     uuid REFERENCES test_participants(id) ON DELETE SET NULL,
    is_augmented       boolean NOT NULL DEFAULT false,
    is_active          boolean NOT NULL DEFAULT true,
    created_at         timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_sign_refs_sign ON sign_references(sign_id);

-- ---------------------------------------------------------------- patient messages

CREATE TABLE patient_messages (
    id                    uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    code                  text UNIQUE NOT NULL,
    urdu_text             text NOT NULL,
    english_text          text,
    kokoro_input          text NOT NULL DEFAULT '',
    audio_asset_id        uuid REFERENCES assets(id) ON DELETE SET NULL,
    audio_source_checksum text,
    priority              priority_level NOT NULL DEFAULT 'p1',
    is_demo_critical      boolean NOT NULL DEFAULT false,
    is_enabled            boolean NOT NULL DEFAULT false,
    reviewed_by           text,
    reviewed_on           date,
    created_at            timestamptz NOT NULL DEFAULT now(),
    updated_at            timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE message_concepts (
    message_id uuid NOT NULL REFERENCES patient_messages(id) ON DELETE CASCADE,
    position   integer NOT NULL,
    sign_id    uuid NOT NULL REFERENCES signs(id) ON DELETE RESTRICT,
    PRIMARY KEY (message_id, position)
);
CREATE INDEX idx_message_concepts_sign ON message_concepts(sign_id);

-- ---------------------------------------------------------------- doctor phrases

CREATE TABLE doctor_phrase_categories (
    id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    code       text UNIQUE NOT NULL,
    name_en    text NOT NULL,
    name_ur    text NOT NULL,
    sort_order integer NOT NULL DEFAULT 0
);

CREATE TABLE doctor_phrases (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    code                text UNIQUE NOT NULL,
    category_id         uuid REFERENCES doctor_phrase_categories(id) ON DELETE SET NULL,
    urdu_text           text NOT NULL,
    english_text        text NOT NULL DEFAULT '',
    psl_asset_id        uuid REFERENCES assets(id) ON DELETE SET NULL,
    verification_status verification_status NOT NULL DEFAULT 'draft',
    verified_by         text,
    verified_on         date,
    priority            priority_level NOT NULL DEFAULT 'p1',
    is_demo_critical    boolean NOT NULL DEFAULT false,
    is_enabled          boolean NOT NULL DEFAULT false,
    sort_order          integer NOT NULL DEFAULT 0,
    stt_aliases         text[] NOT NULL DEFAULT '{}',
    created_at          timestamptz NOT NULL DEFAULT now(),
    updated_at          timestamptz NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------- recognition config and testing

CREATE TABLE recognition_config (
    id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tau_accept     numeric NOT NULL,
    delta_margin   numeric NOT NULL,
    sigma          numeric NOT NULL DEFAULT 0.35,
    band_width_pct numeric NOT NULL DEFAULT 15,
    p_absent       numeric NOT NULL DEFAULT 0.35,
    is_active      boolean NOT NULL DEFAULT false,
    frozen_on      timestamptz,
    frozen_by      uuid REFERENCES users(id),
    notes          text NOT NULL DEFAULT '',
    created_at     timestamptz NOT NULL DEFAULT now()
);
-- I7: exactly one active config
CREATE UNIQUE INDEX idx_recognition_config_active ON recognition_config(is_active) WHERE is_active;

CREATE TABLE recognition_tests (
    id                    uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    test_level            test_level NOT NULL,
    sign_id               uuid NOT NULL REFERENCES signs(id) ON DELETE CASCADE,
    participant_id        uuid REFERENCES test_participants(id) ON DELETE SET NULL,
    attempts              integer NOT NULL,
    correct               integer NOT NULL DEFAULT 0,
    wrong                 integer NOT NULL DEFAULT 0,
    unknown               integer NOT NULL DEFAULT 0,
    top_confusion_sign_id uuid REFERENCES signs(id) ON DELETE SET NULL,
    config_id             uuid REFERENCES recognition_config(id) ON DELETE SET NULL,
    run_on                date NOT NULL DEFAULT current_date,
    notes                 text NOT NULL DEFAULT '',
    created_at            timestamptz NOT NULL DEFAULT now(),
    -- I5: unknown is never folded into wrong
    CONSTRAINT chk_test_totals CHECK (correct + wrong + unknown = attempts),
    CONSTRAINT chk_test_nonneg CHECK (correct >= 0 AND wrong >= 0 AND unknown >= 0 AND attempts > 0)
);
CREATE INDEX idx_tests_sign ON recognition_tests(sign_id);

CREATE TABLE recognition_trials (
    id                   bigserial PRIMARY KEY,
    test_id              uuid NOT NULL REFERENCES recognition_tests(id) ON DELETE CASCADE,
    trial_index          integer NOT NULL,
    ground_truth_sign_id uuid NOT NULL REFERENCES signs(id) ON DELETE CASCADE,
    top1_sign_id         uuid REFERENCES signs(id) ON DELETE SET NULL,
    d1                   numeric,
    d2_diff_label        numeric,
    accepted             boolean NOT NULL DEFAULT false,
    outcome              trial_outcome NOT NULL
);
CREATE INDEX idx_trials_test ON recognition_trials(test_id);

COMMIT;
