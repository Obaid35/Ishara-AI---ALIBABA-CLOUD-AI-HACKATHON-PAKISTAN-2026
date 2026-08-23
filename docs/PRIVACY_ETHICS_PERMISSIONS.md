# Privacy, Ethics & Permissions

## Patient privacy

**The patient has no account and leaves no record.**

- No login, no signup, no identity.
- Camera input is processed for communication and **never permanently stored**. Frames and landmarks live in memory and are discarded.
- No patient table, no medical records, no appointments.
- Session history is shown during a consultation and **cleared when the session ends**. There is no `conversations` table and no stored transcript (D033).

A consultation transcript is identifiable medical information. Keeping it in memory only is both the simpler build and the stronger privacy position. Adding persistence later requires a retention policy, a consent flow and a fresh privacy review — it is not a small change and must not be added quietly.

## Staff accounts

Staff authenticate so the system can offer settings, content management and an audit trail.

- Passwords are hashed, never stored, logged or emailed in plaintext.
- Sessions are revocable — logout and deactivation take effect immediately.
- **No public signup.** Accounts are created internally by an admin.
- Every content change and every login attempt is recorded in the audit log.

The audit log exists to answer one question: *who changed this verified medical phrase, and when.*

## Volunteer recordings

Track permission separately for:

- development/training;
- internal testing;
- demo playback;
- public release.

**Helping the project does not automatically mean permission for public release.** Consent is recorded per purpose against a participant code, with a reference to where the signed form is filed. A recording may be used for a purpose only if a matching granted consent row exists (invariant I8).

Participants are codes (`P01`), never names. There are no name, contact or demographic columns.

## Third-party PSL content

Viewing a public resource and redistributing its video are different activities. If a third-party video is downloaded, embedded, bundled, displayed, or reused, document the permission/licensing basis.

Permission status is a first-class field with four independent usage booleans. A doctor phrase **cannot be enabled** unless its video has demo-playback permission — the database refuses (invariant I2). The permission-gaps report must be empty before the demo.

## Doctor-side importance

Doctor → Patient playback directly displays third-party or verified video content, so content permission is especially important. This is the part of the product most likely to redistribute someone else's work.

## PSL correctness

Priority:

1. Deaf PSL signer / qualified PSL interpreter or knowledgeable reviewer;
2. trusted verified PSL source;
3. remove the phrase if uncertain.

Do not present team improvisation as authoritative medical PSL. The reviewer and date are recorded per sign and per phrase — "someone checked it" is not a record.

## Medical safety

No diagnosis, treatment recommendation, or emergency-triage claim.

Safety behaviours are enforced in the system, not left to discipline:

- the unknown gate can refuse to classify;
- nothing is spoken without explicit patient confirmation;
- a misheard doctor question is confirmed before its video plays;
- unverified content cannot be enabled;
- audio that no longer matches its on-screen text cannot play.

## Transparency

State: limited vocabulary; regional variation; test population size; unknown behaviour as its own number; known limitations; third-party content status; and that Urdu speech uses Kokoro **Hindi** voices rather than an Urdu TTS model.

## Community involvement

At minimum, seek a Deaf PSL user or interpreter review before finalizing the medical vocabulary. **This is part of correctness, not only presentation.**

## Credentials and secrets

- Configuration lives in environment variables; `.env` is gitignored.
- No credential appears in documentation, migrations, source or the audit log.
- Example files contain placeholders only.
- Local development passwords are throwaway values for a local database and must never be reused for anything network-reachable.
