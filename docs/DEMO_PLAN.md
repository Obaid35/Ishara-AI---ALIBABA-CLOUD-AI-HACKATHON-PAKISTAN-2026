# Demo Plan

## Goal

Make the audience understand the human value before explaining the technology.

## Opening

> Imagine reaching a hospital in pain, but the doctor cannot understand your language. PSL Bridge is designed to help with a small but important part of that communication gap.

Do not begin with model or framework names.

# Live consultation

Every step below has a coverage requirement in [Message Map](MESSAGE_MAP.md) §5. All of them must be green before the vocabulary is frozen.

## 1. Patient → Doctor
Patient signs a **verified reliable** medical sign. App shows recognition, builds the Urdu sentence, patient confirms, laptop speaks.

Symptom sign: `CHEST_PAIN`, or `FEVER` under the pain-free fallback.

## 2. Doctor → Patient
Doctor selects `Since when?`; the verified PSL video plays.

## 3. Patient responds
Patient signs `TWO + DAY` — only if those signs are reliable. App responds in Urdu with the duration message.

## 4. One final doctor question
Doctor selects the breathing-difficulty phrase; patient answers `YES` or `NO` — only if reliable.

End. **Do not extend the demo unnecessarily.**

# Optional 15 seconds — only if Tier B/C exists and time allows

Show the admin dashboard: reliable sign count, demo readiness, permission status. It makes the "verified content" claim concrete rather than asserted.

Skip it entirely if the live consultation used more time than planned. The consultation is the demo; the admin console is supporting evidence.

# Explain afterward

- deliberately constrained vocabulary;
- only reliable signs counted;
- existing-video bootstrap was measured on live people;
- unknown/retry is intentional, and tuned to refuse rather than guess;
- Urdu speech uses Kokoro Hindi voices, disclosed;
- no diagnosis;
- runs entirely offline.

# Pre-demo checklist

- [ ] `v_demo_readiness` clear.
- [ ] `v_permission_gaps` empty.
- [ ] No stale audio.
- [ ] Snapshot exported after the last content change.
- [ ] Networking disabled dry run passed.
- [ ] Volume, full-screen, notifications off, charger packed.

# Backup

Record this exact consultation while everything works, on Day 5. Keep a local copy plus a second copy.

Attempt live first; openly use the recording only if venue conditions cause unexpected failure. If a fallback path activates mid-demo, say which one — demonstrating that the fallbacks work is a better answer than pretending nothing broke.

# Rehearsal target

10 exact runs, at least 9 successful without developer intervention. Rehearsal begins only after the vocabulary is frozen.
