# Data Model — PostgreSQL

Schema for the Ishara AI application database. Stack context: [Technology Stack](TECH_STACK.md). Scope tiers and roles: [Application Scope](APPLICATION_SCOPE.md).

## Rules that govern this schema

1. **No patient identity, ever.** There is no patient table, no patient record, no stored consultation. A Deaf patient uses the communication screen without an account (D018).
2. **No patient camera or video sessions are stored by default.** There is no table for them. Landmarks and frames are processed in memory and discarded.
3. **No blobs in the database.** WAV, MP4 and model files live on disk. The database stores path, checksum and metadata.
4. **Content safety is enforced by the schema, not by good intentions.** A message cannot be enabled unless every sign it needs is `Reliable + Enabled`; a doctor phrase cannot be enabled unless its PSL video has demo permission. See [Invariants](#invariants).
5. **Every content change is audited.** Who changed a verified medical phrase, and when, is answerable.

## Entity overview

```text
roles ──< users ──< auth_sessions
                └──< password_resets
                └──< audit_logs

signs ──< sign_variants ──< sign_references ──> assets
      └──< message_concepts >── patient_messages ──> assets (audio)
      └──< recognition_tests ──< recognition_trials
                    └──> test_participants ──< consents

doctor_phrase_categories ──< doctor_phrases ──> assets (psl video)

assets ──1:1── asset_rights

recognition_config          settings
```

## Reference data

### `roles`

| Column | Type | Notes |
|---|---|---|
| `code` | `text` PK | `admin`, `doctor`, `staff` |
| `name` | `text` | display name |
| `description` | `text` | |

Seeded, not user-editable. No `patient` role exists — patients do not authenticate.

### `settings`

| Column | Type | Notes |
|---|---|---|
| `key` | `text` PK | e.g. `primary_output_language`, `english_text_enabled`, `tts_voice`, `overlay_enabled`, `stt_provider` |
| `value` | `jsonb` | |
| `updated_by` | `uuid` FK `users` | |
| `updated_at` | `timestamptz` | |

## Identity and access

### `users`

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `email` | `citext` UNIQUE | login identifier |
| `username` | `citext` UNIQUE NULL | optional alternative |
| `password_hash` | `text` | Argon2id or bcrypt — never plaintext, never reversible |
| `full_name` | `text` | |
| `role_code` | `text` FK `roles` | |
| `is_active` | `boolean` default `true` | deactivation is instant, not deletion |
| `must_change_password` | `boolean` default `true` | admin-created accounts start here |
| `last_login_at` | `timestamptz` NULL | |
| `created_by` | `uuid` FK `users` NULL | accounts are created internally |
| `created_at` / `updated_at` | `timestamptz` | |

**There is no public signup.** No self-registration endpoint exists. Accounts are created by an admin ([Application Scope](APPLICATION_SCOPE.md)).

### `auth_sessions`

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `user_id` | `uuid` FK `users` | |
| `refresh_token_hash` | `text` | hash only |
| `issued_at` / `expires_at` | `timestamptz` | |
| `revoked_at` | `timestamptz` NULL | set on logout |
| `user_agent` / `ip` | `text` NULL | |

Short-lived access token plus a revocable refresh session, so that logout and "disable this user" take effect immediately rather than at token expiry.

### `password_resets`

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `user_id` | `uuid` FK `users` | |
| `token_hash` | `text` | hash only |
| `expires_at` | `timestamptz` | short window |
| `used_at` | `timestamptz` NULL | single use |

### `audit_logs`

| Column | Type | Notes |
|---|---|---|
| `id` | `bigserial` PK | |
| `user_id` | `uuid` FK `users` NULL | null for system actions |
| `action` | `text` | `create`, `update`, `enable`, `disable`, `login`, `login_failed`, `export_snapshot`, `freeze_thresholds` |
| `entity_type` | `text` | `sign`, `patient_message`, `doctor_phrase`, `asset`, `user`, `recognition_config` |
| `entity_id` | `text` NULL | |
| `before` / `after` | `jsonb` NULL | changed fields only |
| `ip` | `inet` NULL | |
| `created_at` | `timestamptz` | |

Append-only. Never updated, never deleted from the application. Content changes to verified medical material and any threshold freeze **must** be audited.

## Vocabulary

### `signs`

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `code` | `text` UNIQUE | `FEVER`, `CHEST_PAIN`, `YES` — the identifier used everywhere else |
| `urdu_meaning` | `text` | |
| `english_meaning` | `text` | |
| `verification_status` | `enum` | `draft`, `psl_verified`, `rejected` |
| `reliability_status` | `enum` | `candidate`, `experimenting`, `testing`, `reliable`, `weak`, `dropped` |
| `is_enabled` | `boolean` default `false` | in production vocabulary |
| `verified_by` | `text` NULL | signer / interpreter / source |
| `verified_on` | `date` NULL | |
| `regional_variant_note` | `text` NULL | |
| `delta_margin_override` | `numeric` NULL | **stricter only** — see [Recognition Spec](RECOGNITION_SPEC.md) §7 |
| `is_demo_critical` | `boolean` default `false` | required by the demo script |
| `notes` | `text` | known confusions |

The two status columns are deliberately separate: **linguistic correctness** and **recognition reliability** are different questions with different reviewers. A sign can be perfectly verified PSL and still be technically weak, and it must then be excluded.

The status workflow ([Admin Specification](ADMIN_SPEC.md)):

```text
draft → psl_verified → testing → reliable → enabled
                          ↓
                     weak / dropped → disabled
```

Only `reliability_status = 'reliable' AND is_enabled = true` enters the production vocabulary. Only those signs are counted in any number quoted to judges (D009).

### `sign_variants`

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `sign_id` | `uuid` FK `signs` | |
| `label` | `text` | e.g. `standard`, `karachi`, `two-handed` |
| `region_note` | `text` NULL | |
| `is_default` | `boolean` | |
| `is_enabled` | `boolean` | |

Regional variation is a documented limitation, not a silent assumption. A variant is a first-class row so we can state exactly which variants we support.

### `sign_references`

The DTW reference clips and their extracted landmark sequences. Directly consumed by [Recognition Spec](RECOGNITION_SPEC.md).

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `sign_id` | `uuid` FK `signs` | |
| `variant_id` | `uuid` FK `sign_variants` NULL | |
| `asset_id` | `uuid` FK `assets` | the source clip |
| `landmark_path` | `text` | extracted sequence on disk |
| `landmark_checksum` | `text` | |
| `extractor_version` | `text` | MediaPipe version + API used |
| `frame_count` | `int` | |
| `source_fps` | `numeric` | |
| `participant_id` | `uuid` FK `test_participants` NULL | null for dictionary sources |
| `is_augmented` | `boolean` default `false` | augmented variant, not a new signer |
| `is_active` | `boolean` default `true` | |

`extractor_version` exists because reference clips and live input **must** be processed by the identical extraction path. If the extractor version changes, every reference must be re-extracted — this column is what makes that detectable instead of silently wrong.

`is_augmented` keeps the honest-reporting rule enforceable: augmented references are never counted as signer diversity (D006).

## Patient messages

### `patient_messages`

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `code` | `text` UNIQUE | `CHEST_PAIN_TWO_DAYS` |
| `urdu_text` | `text` | shown on screen |
| `english_text` | `text` NULL | optional toggle |
| `kokoro_input` | `text` | **Devanagari** pronunciation string for TTS |
| `audio_asset_id` | `uuid` FK `assets` NULL | pre-generated WAV |
| `audio_source_checksum` | `text` NULL | hash of `urdu_text` + `kokoro_input` at generation time |
| `priority` | `enum` | `p0`, `p1`, `p2` |
| `is_demo_critical` | `boolean` | |
| `is_enabled` | `boolean` default `false` | |
| `reviewed_by` | `text` NULL | fluent Urdu speaker |
| `reviewed_on` | `date` NULL | |

**`audio_source_checksum` is the staleness guard.** If it does not match the current hash of `urdu_text` + `kokoro_input`, the WAV was generated from different text and must be regenerated. Without this column, an edited sentence silently keeps playing the old audio — which in a medical context means the screen and the speaker say different things.

### `message_concepts`

| Column | Type | Notes |
|---|---|---|
| `message_id` | `uuid` FK `patient_messages` | |
| `position` | `int` | 1-based, ordered |
| `sign_id` | `uuid` FK `signs` | |
| PK | (`message_id`, `position`) | |

The recognised concept sequence that produces the message. `CHEST_PAIN + TWO + DAY` is three rows. Lookup is exact-sequence; an unmatched sequence shows recognised concepts and no invented sentence.

## Doctor phrases

### `doctor_phrase_categories`

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `code` | `text` UNIQUE | `basic`, `pain`, `symptoms`, `medical` |
| `name_en` / `name_ur` | `text` | |
| `sort_order` | `int` | |

### `doctor_phrases`

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `code` | `text` UNIQUE | `DOCTOR_SINCE_WHEN` |
| `category_id` | `uuid` FK | |
| `urdu_text` / `english_text` | `text` | doctor-facing label |
| `psl_asset_id` | `uuid` FK `assets` | verified PSL video |
| `verification_status` | `enum` | `draft`, `psl_verified`, `rejected` |
| `verified_by` | `text` NULL | signer / interpreter — never an unqualified team member (D013) |
| `verified_on` | `date` NULL | |
| `priority` | `enum` | `p0`, `p1`, `p2` |
| `is_demo_critical` | `boolean` | |
| `is_enabled` | `boolean` default `false` | |
| `sort_order` | `int` | |
| `stt_aliases` | `text[]` | spoken Urdu phrasings that map here (P1 voice input) |

`stt_aliases` supports doctor voice input without ever letting speech generate PSL: transcribed speech is matched against this closed list, the match is shown for confirmation, then the verified video plays.

## Assets and rights

A single `assets` table with a `kind` discriminator, rather than separate `psl_assets` and `audio_assets` tables. One table means **one permission-tracking path** — a separate audio table would eventually acquire its own half-maintained rights columns. Compatibility views `psl_assets` and `audio_assets` are provided.

### `assets`

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `kind` | `enum` | `psl_video`, `audio_wav`, `reference_clip` |
| `path` | `text` UNIQUE | relative to repo root |
| `checksum` | `text` | |
| `bytes` | `bigint` | |
| `duration_ms` | `int` NULL | |
| `created_at` | `timestamptz` | |

### `asset_rights`

One row per asset. Mirrors the permission buckets in [Data Strategy](DATA_STRATEGY.md) and [Privacy, Ethics & Permissions](PRIVACY_ETHICS_PERMISSIONS.md).

| Column | Type | Notes |
|---|---|---|
| `asset_id` | `uuid` PK FK `assets` | |
| `source_name` | `text` | owner / origin |
| `source_url` | `text` NULL | |
| `permission_status` | `enum` | `unknown`, `requested`, `granted`, `denied`, `own_recording` |
| `permitted_development` | `boolean` default `false` | |
| `permitted_internal_testing` | `boolean` default `false` | |
| `permitted_demo_playback` | `boolean` default `false` | |
| `permitted_public_release` | `boolean` default `false` | |
| `requested_on` / `responded_on` | `date` NULL | |
| `license_notes` | `text` NULL | |
| `evidence_ref` | `text` NULL | where the reply is filed |

The four booleans are separate because they are genuinely separate permissions. Helping the project does not imply consent to public release, and viewing a public video does not imply the right to redistribute it.

## Testing and calibration

### `test_participants`

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `participant_code` | `text` UNIQUE | `P01`, `P02` — matches `SIGNCODE_P03_R07` |
| `is_unseen` | `boolean` | never used for tuning — the T4 population |
| `notes` | `text` NULL | non-identifying only |

Deliberately no name, contact or demographic columns. A participant is a code.

### `consents`

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `participant_id` | `uuid` FK | |
| `purpose` | `enum` | `development`, `internal_testing`, `demo_playback`, `public_release` |
| `granted` | `boolean` | |
| `granted_on` | `date` | |
| `evidence_ref` | `text` | where the signed form is filed |

One row per purpose per participant. A recording may be used for a purpose **only** if a matching `granted = true` row exists.

### `recognition_tests`

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `test_level` | `enum` | `t1_source`, `t2_live_team`, `t3_second_person`, `t4_unseen`, `t5_room_variation` |
| `sign_id` | `uuid` FK `signs` | |
| `participant_id` | `uuid` FK NULL | |
| `attempts` | `int` | the denominator, always recorded |
| `correct` / `wrong` / `unknown` | `int` | **three separate counts** |
| `top_confusion_sign_id` | `uuid` FK `signs` NULL | |
| `config_id` | `uuid` FK `recognition_config` | thresholds in force |
| `run_on` | `date` | |
| `notes` | `text` | |

`correct + wrong + unknown = attempts` is a check constraint. Unknown is never folded into wrong, and no accuracy figure is ever stored without its denominator.

### `recognition_trials`

Per-trial detail. This table is what makes threshold calibration possible ([Recognition Spec](RECOGNITION_SPEC.md) §5) — without per-trial distances there is nothing to calibrate against.

| Column | Type | Notes |
|---|---|---|
| `id` | `bigserial` PK | |
| `test_id` | `uuid` FK `recognition_tests` | |
| `trial_index` | `int` | |
| `ground_truth_sign_id` | `uuid` FK `signs` | |
| `top1_sign_id` | `uuid` FK `signs` NULL | |
| `d1` | `numeric` | best normalised DTW distance |
| `d2_diff_label` | `numeric` NULL | best distance carrying a **different** sign code |
| `accepted` | `boolean` | did the unknown gate accept |
| `outcome` | `enum` | `correct`, `wrong`, `unknown_ambiguous`, `unknown_no_match` |

### `recognition_config`

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `tau_accept` | `numeric` | absolute quality threshold |
| `delta_margin` | `numeric` | separation from best different label |
| `sigma` | `numeric` | display-similarity scaling only |
| `band_width_pct` | `numeric` | Sakoe–Chiba band |
| `p_absent` | `numeric` | missing-hand penalty |
| `is_active` | `boolean` | exactly one active row |
| `frozen_on` | `timestamptz` NULL | |
| `frozen_by` | `uuid` FK `users` NULL | |
| `notes` | `text` | |

Thresholds are rows, not constants in code, so that "which thresholds produced this result" is always answerable. Freezing writes `frozen_on` and an audit entry. **Changing an active frozen config after a T4 run voids that T4 result** — the rule is in [Recognition Spec](RECOGNITION_SPEC.md) §6 and the audit log is the evidence.

## Conversation history — intentionally not a table

Session history is shown during a consultation and **cleared when the session ends** ([Application Scope](APPLICATION_SCOPE.md) §Session history). It lives in browser/server memory only.

There is no `conversations` table, no `messages_sent` table and no transcript storage. A consultation transcript is identifiable medical information; the hackathon and the privacy position are both far simpler if it never reaches disk. If it is ever added, it requires a fresh privacy review, a retention policy and a consent flow — it is not a small change.

## Invariants

Enforced by check constraints, triggers or application-level validation with tests. These encode the project's safety rules in the one place that cannot be forgotten under deadline pressure.

| # | Invariant |
|---|---|
| I1 | A `patient_message` may be `is_enabled` only if **every** sign in its `message_concepts` is `reliability_status = 'reliable' AND is_enabled = true`. |
| I2 | A `doctor_phrase` may be `is_enabled` only if `verification_status = 'psl_verified'` **and** its PSL asset has `permitted_demo_playback = true`. |
| I3 | A `patient_message` with an `audio_asset_id` is playable only if `audio_source_checksum` matches the current hash of `urdu_text` + `kokoro_input`. |
| I4 | `signs.delta_margin_override`, when set, must be **stricter** than the active `recognition_config.delta_margin`. |
| I5 | `recognition_tests`: `correct + wrong + unknown = attempts`. |
| I6 | A `sign_reference` may be active only if its source asset has `permitted_development = true`. |
| I7 | Exactly one `recognition_config` row has `is_active = true`. |
| I8 | A recording may be used for a purpose only if a matching granted `consents` row exists. |

I1 is the one that prevents the failure I would otherwise expect on Day 6: a message quietly reaching the demo while one of its signs was removed for being weak.

## Views

| View | Purpose |
|---|---|
| `v_production_vocabulary` | signs that are `reliable + enabled` — the only count quoted publicly |
| `v_demoable_messages` | messages satisfying I1 and I3 |
| `v_demoable_doctor_phrases` | phrases satisfying I2 |
| `v_permission_gaps` | assets in use whose rights are `unknown` or `requested` |
| `v_demo_readiness` | demo-critical signs, messages and phrases that are not yet demoable |
| `psl_assets` / `audio_assets` | compatibility views over `assets` by kind |

`v_demo_readiness` is the query the team runs each morning instead of guessing.

## JSON snapshot export

The backend must be able to boot without PostgreSQL ([Technology Stack](TECH_STACK.md) §12). A CLI task exports the demoable views to:

```text
data/
  signs.json
  messages.json
  doctor_phrases.json
```

- Exported at feature freeze and re-exported after any content change.
- Contains only enabled, demoable content — the export is filtered through the invariants, so an unverified phrase cannot leak into the fallback path.
- Contains no user rows, no participant rows, no consent records, no audit log.
- Snapshot mode is **read-only**: recognition, messages, audio and doctor playback work; admin editing and test recording require the live database.
- Each export writes an `export_snapshot` audit entry.

## Migrations and seed

- Migrations live in `db/migrations`, applied in order, never edited after being applied.
- `db/seed` provides roles, the initial admin account, phrase categories, and the candidate vocabulary from [Message Map](MESSAGE_MAP.md) with `is_enabled = false`.
- **Seed data is never enabled by default.** Content becomes enabled only by passing verification, which is a human decision recorded in the audit log.
