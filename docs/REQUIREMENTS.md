# Requirements

## Priority definitions

- **P0:** cannot demo without it.
- **P1:** valuable, but cuttable.
- **P2:** stretch only.

Scope tiers are in [Application Scope](APPLICATION_SCOPE.md). Tier A is P0; the application shell and admin console are P1/P2 and are cut before anything in Tier A.

# P0 — Must have

## Patient → Doctor
- Live camera.
- Patient uses the communication screen **without any account or login**.
- Complete-sign recognition behavior (one motion → at most one decision).
- Unknown/retry state with both conditions of the unknown gate.
- Confirm-before-speak.
- Urdu text.
- Urdu speech from pre-generated local audio.
- Undo last sign.
- Clear message.
- At least 10 useful medical messages.
- At least one unseen signer tested.

## Doctor → Patient
- Fixed doctor phrase library, grouped by category.
- At least 10 verified PSL responses.
- Play/replay video.
- Clear return to Patient mode.

## Engineering
- Stack as frozen in [Technology Stack](TECH_STACK.md).
- PostgreSQL schema with content invariants enforced ([Data Model](DATA_MODEL.md)).
- JSON snapshot export so the app boots if PostgreSQL is unavailable.
- Configuration from environment variables; no credential in source or docs.
- **Entire P0 demo runs with the network adapter disabled** — verified, not assumed.

## Quality
- Exact demo works 9/10 rehearsals.
- Per-person test matrix exists.
- Recognition thresholds calibrated and frozen before the unseen-person test.
- Backup demo video exists.
- Permission/rights status documented for every displayed asset.
- PSL wording reviewed by a knowledgeable signer/interpreter where possible.
- Urdu wording reviewed by a fluent Urdu speaker; generated audio verified **by ear**.

# P1 — Should have

## Application shell
- Staff login (doctor / nurse / admin) with hashed passwords and revocable sessions.
- Role-based access enforced server-side.
- Forgot-password flow.
- Session history, temporary and cleared at session end.
- `+ New Conversation`.
- Settings screen.

## Admin console
- Dashboard with demo-readiness and permission-gap tiles.
- Signs, patient messages and doctor phrases management.
- Sign verification workflow.
- Recognition test records.
- Assets and permissions tracking.
- User management (no public signup).
- Audit log.

## Communication features
- Doctor Urdu voice input via Groq `whisper-large-v3-turbo`, matched to approved phrases with confirm-before-play.
- Offline STT fallback (faster-whisper `small`, INT8).
- Phrase search and categories.
- Full-screen PSL video.
- 15 doctor phrases.
- 15 patient message outcomes.
- 20–30 reliable signs.
- Tracking overlay.
- Clean visual status colors.
- English text toggle.

# P2 — Stretch

- 30–40 reliable signs.
- English speech via the same Kokoro system.
- Doctor Urdu speech mapped to a larger verified PSL phrase inventory.
- LLM sentence generation for unsupported concept combinations, constrained to communication output only (Groq `openai/gpt-oss-20b`, structured output).
- Regional variants.
- Mobile polish.

# Out of scope

- **Patient accounts** — permanent decision, not a deferral.
- **Public signup** — accounts are created internally by an admin.
- Patient medical records.
- Stored consultation transcripts (requires a separate privacy review).
- Appointments and billing.
- Hospital administration beyond content management.
- Organisation hierarchy / multi-tenant.
- SSO.
- Full continuous PSL translation.
- AI diagnosis or treatment advice.
- Generated PSL avatar.
- Full unrestricted Urdu → PSL.
