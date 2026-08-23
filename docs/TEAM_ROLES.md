# Team Roles

Example four-person ownership. Names go in [Project Status](PROJECT_STATUS.md) — a role with no name attached is not owned.

## 1 — PSL / Data Lead
Owns sign search, vocabulary verification, permissions, volunteer scheduling, recording quality, and Deaf signer/interpreter coordination.

**Named critical path: pain-concept PSL verification, due end of Day 2** (D015). Three signs, the flagship message and half the message library depend on the answer.

Also owns: reference clip preparation, `extractor_version` discipline, asset rights records, and participant consent per purpose.

## 2 — Recognition Lead
Owns the Day-1 experiment, MediaPipe extraction, DTW matching, segmentation behaviour, the unknown gate, threshold calibration and the freeze, and confusion analysis.

Also owns the frame-latency measurement on Day 1 and the decision on the browser-extraction contingency (D035).

## 3 — Product / Web Lead
Owns the one-screen app, camera UX, mode switch, message UI, controls, Urdu output integration, doctor PSL playback, the FastAPI backend, the PostgreSQL schema and invariants, and the JSON snapshot export.

If the application shell and admin console are built, they are owned here — **after** Tier A is stable.

## 4 — UX / QA / Presentation Lead
Owns Urdu wording, `kokoro_input` authoring and the by-ear audio verification, the Kokoro voice blind test, design consistency, the test matrix, the demo script, reliability rehearsal, evidence, and judge Q&A.

## Shared responsibilities

Everyone helps test, does not invent PSL without verification, reports failures honestly, and prioritizes P0 over polish.

**Nobody loosens a threshold, enables unverified content, or edits a message without regenerating its audio** — regardless of deadline pressure. These are the rules the database enforces precisely because people under pressure would otherwise break them.

## Daily 15-minute sync

Answer only:

1. What works?
2. What failed?
3. Highest-risk blocker?
4. What do we cut today if needed?
5. What must be proven before tomorrow?

Question 5 requires a **measurable** answer. "Work on recognition" is not one; "FEVER at 8/10 on a second person" is.

## The standing warning

The scope now includes authentication, an admin console and a database. None of that is Tier A. If the login screen exists before an unseen person has successfully signed, the project is failing regardless of how much has been built.
