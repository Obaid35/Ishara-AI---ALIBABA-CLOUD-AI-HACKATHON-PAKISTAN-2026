# Admin Console Specification

Tier C of [Application Scope](APPLICATION_SCOPE.md). Admin-only. Backed by the schema in [Data Model](DATA_MODEL.md).

## Purpose

The admin console exists so that **verified medical content is managed deliberately and traceably** instead of living in hardcoded lists that anyone can edit at 3 a.m. before a demo.

Its most important job is not CRUD. It is enforcing that only verified, permitted, tested content reaches a patient.

## Guard rails

Every screen below obeys these:

1. **Nothing is enabled by default.** New content is created disabled and becomes enabled only by a human decision that is audited.
2. **The invariants are enforced server-side.** The UI may grey out an impossible action, but the server rejects it regardless — I1–I8 in [Data Model](DATA_MODEL.md).
3. **Every mutation writes an audit entry** with before/after values.
4. **Disable, never delete.** Content that reached a patient is deactivated, not erased.
5. **Danger is explained inline.** When enabling is blocked, the screen says *why* — "STOMACH_PAIN is not Reliable" — not "invalid".

## `/admin` — Dashboard

The morning status page. Everything here is a query, not a manual tally.

| Tile | Source |
|---|---|
| Reliable + Enabled signs | `v_production_vocabulary` count |
| Signs by status | `signs` grouped by `reliability_status` |
| Verified vs unverified signs | `signs.verification_status` |
| Demoable patient messages | `v_demoable_messages` count |
| Demoable doctor phrases | `v_demoable_doctor_phrases` count |
| **Demo readiness** | `v_demo_readiness` — demo-critical items not yet demoable |
| Permission gaps | `v_permission_gaps` — assets in use with rights `unknown`/`requested` |
| Recent test results | latest `recognition_tests` rows |
| Active thresholds | `recognition_config` where `is_active`, with frozen state |

**Demo readiness and permission gaps are the two tiles that matter.** They replace the two questions the team would otherwise answer by guessing: *will the demo work* and *are we allowed to show this video*.

The reliable-sign tile is the only number that may be quoted publicly ([Judge Q&A](JUDGE_QA.md)).

## `/admin/signs`

List: code · Urdu · English · verification status · reliability status · enabled · demo-critical · variants · reference count.

Filters: status, enabled, demo-critical, verification risk.

### Sign detail

- code, Urdu meaning, English meaning
- verification status, verified by, verified on
- reliability status
- regional variant note
- `delta_margin_override` — **stricter only**; the form rejects a looser value (I4)
- demo-critical flag
- confusion notes
- enable / disable
- variants list
- reference clips list with source asset, extractor version, augmented flag, active flag

### Verification workflow

```text
draft → psl_verified → testing → reliable → enabled
                          ↓
                     weak / dropped → disabled
```

Rules enforced by the console:

- `psl_verified` requires `verified_by` and `verified_on`. Verification is by a Deaf PSL signer, qualified interpreter, or a trusted verified source — never an unqualified team member (D013).
- A sign cannot reach `reliable` without at least one recorded `recognition_tests` row from a **different person** than any used for tuning.
- `enabled` requires `reliable`.
- Setting a sign to `weak` or `dropped` **automatically disables every patient message that depends on it** (I1 cascade) and the console shows exactly which messages will be affected **before** confirming.

That last rule is the one that prevents the Day-5 failure mode: removing a weak sign and only discovering during rehearsal that three demo messages silently broke.

### Reference clips

Upload or register a reference clip, extract landmarks, view frame count and duration. Displays `extractor_version` prominently — if it differs from the current MediaPipe version, the row is flagged **stale** and must be re-extracted before it is trusted ([Recognition Spec](RECOGNITION_SPEC.md) §1).

Augmented references are visually distinct from real performances and never counted as signer diversity (D006).

## `/admin/messages`

List: code · concept sequence · Urdu · priority · enabled · audio status.

### Message detail

- concept sequence builder — ordered picker over `signs`, showing each concept's reliability status inline
- `urdu_text`, `english_text`
- `kokoro_input` (Devanagari)
- reviewed by / reviewed on
- audio: file, duration, **generate**, **regenerate**, play
- priority, demo-critical, enable/disable

### Audio staleness

The screen compares the stored `audio_source_checksum` with a live hash of `urdu_text` + `kokoro_input`. On mismatch it shows:

> ⚠ **Audio is stale.** The text changed after this audio was generated. Regenerate before the demo.

and playback is blocked from the demo path (I3). A screen that reads one sentence while the speaker says another is a medical-safety failure, not a cosmetic bug.

Enable is blocked while any concept is not `Reliable + Enabled`, with the blocking concepts named.

## `/admin/doctor-phrases`

List: category · code · Urdu · English · verification · permission status · enabled · demo-critical.

Grouped by the categories in [Message Map](MESSAGE_MAP.md) §7 — Basic, Pain, Symptoms, Medical — with drag-to-reorder within a category, because doctor-side speed depends on layout.

### Phrase detail

- category, code, Urdu, English
- PSL video asset with inline playback
- verification status, verified by, verified on
- permission status pulled from `asset_rights`
- `stt_aliases` — spoken Urdu phrasings that map to this phrase (P1 voice input)
- priority, demo-critical, enable/disable

Enable requires `psl_verified` **and** `permitted_demo_playback = true` on the video (I2). Both conditions are shown as a two-line checklist so a blocked enable is self-explanatory.

## `/admin/testing`

Where the project's evidence lives. Feeds [Testing Plan](TESTING_PLAN.md) and threshold calibration.

### Record a test

Test level (T1–T5) · sign · participant · attempts · correct · wrong · unknown · top confusion · notes.

`correct + wrong + unknown = attempts` is validated on the form (I5). **Unknown is never merged into wrong** — they are different behaviours and the project reports them separately.

### Views

- per-sign matrix across participants, matching the [Testing Plan](TESTING_PLAN.md) grid, with ✅ / ❌ / ?
- per-participant results, unseen participants marked
- confusion pairs ranked by frequency
- Day-1 experiment summary with its 100-trial denominator
- every accuracy figure displayed **with its denominator**, never as a bare percentage

### Threshold calibration

Reads `recognition_trials` to plot `d1` and margin distributions for correct versus incorrect top-1, and proposes `tau_accept` / `delta_margin` at the required operating point — wrong-accepts ≤ 2% first, then maximise correct-accepts ([Recognition Spec](RECOGNITION_SPEC.md) §5).

**Freeze thresholds** is an explicit, audited action. After freezing, the console warns on any attempt to change them:

> Changing frozen thresholds voids the T4 unseen-person result recorded on `<date>`.

## `/admin/assets`

List: kind · path · used by · source · permission status · permitted usages · checksum.

### Asset detail

- file metadata, checksum, duration, inline preview
- source name and URL
- permission status: `unknown` / `requested` / `granted` / `denied` / `own_recording`
- four independent permission booleans: development · internal testing · demo playback · public release
- requested on / responded on
- licence notes, evidence reference

The four booleans are separate because they are separate permissions. Helping the project does not imply consent to public release, and viewing a public video does not imply the right to redistribute it.

**Permission gaps report:** every asset currently referenced by enabled content whose rights are `unknown` or `requested`. This is the list that must be empty before the demo, and it is the evidence for the rights question in [Acceptance Criteria](ACCEPTANCE_CRITERIA.md).

### Participants and consent

Participants are codes (`P01`), never names. Per-participant consent rows for each of the four purposes, with the evidence reference for the signed form. A recording may be used for a purpose only if a matching granted consent exists (I8).

## `/admin/users`

List: name · email · role · active · last login · created by.

Actions: create doctor/staff/admin account · reset password · activate/deactivate · change role.

- **No public registration.** Accounts are created here only.
- New accounts start with `must_change_password = true`.
- Deactivation revokes active sessions immediately.
- An admin cannot deactivate or demote their own account — prevents locking the system out of administration.
- Passwords are never displayed, never emailed in plaintext, never written to the audit log.

## `/admin/audit`

Append-only log: timestamp · user · action · entity · before/after diff.

Filterable by user, entity type and date. Never editable, never deletable from the application.

The entries that matter most: content enable/disable, verification status changes, threshold freezes, permission changes, user role changes, and snapshot exports.

## `/settings`

Application settings from [Application Scope](APPLICATION_SCOPE.md) §Settings. Admin only.

Changing the TTS voice marks **all** pre-generated audio stale, because every WAV was produced by the previous voice. The screen states this before saving and lists how many files will need regeneration.

## Snapshot export

A dashboard action exports the demoable views to `data/*.json` for the offline fallback path ([Technology Stack](TECH_STACK.md) §12).

The export is filtered through the invariants, so unverified or unpermitted content cannot leak into the fallback. The screen shows the last export time and warns when content has changed since — a stale snapshot restoring deleted weak signs mid-demo is precisely the failure this must not cause.

## What the admin console must never do

- Never allow enabling content that fails an invariant, even "just for the demo".
- Never allow a looser per-sign threshold.
- Never allow editing or deleting audit entries.
- Never surface patient data — there is none.
- Never let a user with a non-admin role reach these endpoints, regardless of what the UI shows.
