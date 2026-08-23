# Contributing / Team Rules

## The stack is frozen

Do not substitute a technology without a **measured failure** or a **documented reason** recorded in the [Decision Log](DECISIONS_LOG.md). "I found something newer" is not a reason. See [Technology Stack](TECH_STACK.md).

Pinned versions are not upgraded during the build. A MediaPipe upgrade invalidates every extracted reference.

## Before adding a sign

- identify verified PSL meaning, record `verified_by` and `verified_on`;
- record its source and rights status;
- confirm it is needed by an actual message or the demo script;
- test live on a **different person**;
- document confusions;
- confirm it passes the gate without a loosened threshold.

## Before adding a feature

Ask:

1. Is Tier A stable — has an unseen person signed successfully?
2. Does this improve the medical communication?
3. Can it be completed and tested before freeze?

If not, do not add it. Admin and shell features are Tier B/C and are cut first.

## Before changing content

- **Editing `urdu_text` or `kokoro_input` invalidates the audio.** Regenerate and re-verify by ear before the demo. The checksum guard will block playback, but do not rely on discovering it during rehearsal.
- Disabling a sign auto-disables dependent messages. Check what will break before confirming.
- A doctor phrase label may be reworded; **the PSL video may never be swapped without re-verification.**
- Re-export the JSON snapshot after any content change.

## Never

- Never commit `.env` or put a credential in docs, migrations, source or the audit log.
- Never enable content that fails an invariant, even "just for the demo".
- Never loosen a per-sign threshold.
- Never change frozen thresholds after T4 without voiding and re-reporting that result.
- Never merge unknown counts into wrong counts.
- Never quote a sign count that includes experimental signs.

## Review checklist

- [ ] Patient safety behavior unaffected.
- [ ] Unknown handling still works — both conditions.
- [ ] Confirm-before-speak still works.
- [ ] One motion still produces at most one decision.
- [ ] Patient can still use `/` with no login.
- [ ] One-screen layout still fits on `/`.
- [ ] Urdu remains readable.
- [ ] New PSL phrase verified.
- [ ] Third-party asset permitted for its usage.
- [ ] Audio checksums current.
- [ ] Admin routes still reject non-admin roles server-side.
- [ ] Exact demo regression tested.

## Freeze rule

After Day 5: no new vocabulary except replacing a broken sign; no new Tier B/C features; only blockers, reliability, wording, permissions, and rehearsal.

Thresholds are frozen **before** the unseen-person test, which is earlier than the vocabulary freeze.

## Cut order

Admin console → application shell → English toggle → doctor voice input → skeleton overlay → extra doctor phrases → weak signs.

Never cut: unknown handling, confirm-before-speak, unseen-person testing, threshold freeze, final rehearsal, offline dry run.
