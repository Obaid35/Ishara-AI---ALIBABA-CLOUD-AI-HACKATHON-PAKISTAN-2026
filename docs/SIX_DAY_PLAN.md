# Six-Day Execution Plan

## Scheduling note

The **sequence** is authoritative. If calendar dates shift, keep the order. If the competition starts before a full sixth build day is available, treat Day 5 as the practical feature freeze.

Scope has grown to include authentication, an admin console and PostgreSQL. **That work is Tier B/C and does not move ahead of Tier A** ([Application Scope](APPLICATION_SCOPE.md), D036).

# Day 1 — Prove the bootstrap strategy

## Objective
Determine whether existing PSL dictionary videos can bootstrap useful live recognition.

## Work
- install and pin the frozen stack; record versions;
- verify the Kokoro Hindi path actually runs;
- measure camera → backend latency and record it;
- lock healthcare scope;
- pick the 5 Day-1 signs from the freeze list (`YES` `NO` `HELP` `FEVER` `COUGH`);
- prepare complete sign performances;
- run DTW reference matching;
- run the augmented-reference experiment;
- run 100 live trials, logging per-trial distances;
- calibrate `τ_accept` and `δ_margin`;
- blind listening test across the four Kokoro Hindi voices;
- recruit volunteers in parallel;
- send the permission request;
- **start pain-concept PSL verification**.

## Exit
Choose one: existing-video-first viable / needs targeted recordings / insufficient. Plus: latency recorded, voice chosen, thresholds calibrated.

# Day 2 — Scale carefully

If Day 1 is strong: expand 5 → 10–15 and retest.
If medium: add examples only for weak signs.
If poor: begin verified volunteer recordings immediately.

Also due:
- **pain-concept verification resolved** — if not, switch to the pain-free P0 message set (D024);
- Urdu strings drafted and reviewed for the P0 messages;
- `kokoro_input` authored; first audio generated and checked by ear.

Exit with a stable data strategy and the first reliable sign set.

# Day 3 — Complete Patient → Doctor

Must work end-to-end:
- live sign;
- recognised concept;
- unknown/retry, both conditions;
- Urdu message from templates;
- patient confirmation;
- Urdu speech from pre-generated audio.

If unstable, **do not build P1 features** — no login, no admin, no database migration work.

# Day 4 — Two-way communication and the data layer

Add:
- doctor phrase library with categories and search;
- verified PSL playback;
- Undo/Clear;
- polished one-screen UI;
- controlled message patterns;
- PostgreSQL schema, migrations, seed, and the content invariants;
- JSON snapshot export;
- tracking overlay only if the core is stable.

Tier B shell (login, roles, session history, settings) starts only once the above is done.

# Day 5 — Unseen-person testing and freeze

- **freeze thresholds before testing begins**;
- bring a person not used for tuning;
- run the per-sign matrix;
- remove weak signs — dependent messages auto-disable;
- improve critical confusions;
- regenerate any stale audio;
- re-export the JSON snapshot;
- run the full consultation;
- record the backup demo video;
- **freeze the vocabulary at end of day**.

Admin console work happens here only if everything above is complete.

No major new features afterward.

# Day 6 — Reliability and presentation

- fix demo blockers only;
- verify permission status — `v_permission_gaps` empty;
- verify Urdu and PSL content;
- **full dry run with networking disabled**;
- run the exact demo 10 times, target 9/10;
- finalise pitch and Q&A.

Vocabulary is already frozen from Day 5 — **rehearsal cannot begin while signs are still being removed**, which is why the freeze moved a day earlier.

## Cut order

1. Admin console (Tier C)
2. Application shell — login, settings, history (Tier B)
3. English toggle
4. Doctor voice input
5. Skeleton overlay
6. Extra doctor phrases
7. Weak signs

## Never cut

- unknown handling;
- confirm-before-speak;
- unseen-person testing;
- threshold freeze before T4;
- final rehearsal;
- offline dry run.
