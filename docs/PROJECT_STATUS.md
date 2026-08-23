# Project Status

Use this file as the daily truth source. Fill it in — an unfilled status file is worse than none, because it looks like information.

## Current stage

`Planning` / Day 1 / Day 2 / Day 3 / Day 4 / Day 5 / Day 6 / Demo Ready

**Last updated:** 2026-08-23 (application built)
**Updated by:** _(name)_

## Tier A — communication core (P0, never cut)

| Item | Status | Owner | Blocker |
|---|---|---|---|
| Stack installed and running end-to-end | **Done** | | |
| Kokoro Hindi install verified | Not started | | |
| Kokoro voice chosen by blind test | Not started | | |
| 5-sign Day-1 experiment | Not started | | |
| 100 live trials | Not started | | |
| Data strategy decision | Not started | | |
| Frame-latency measurement recorded | Not started | | |
| Patient live camera | **Done** | | |
| Sign segmentation (one motion → one decision) | **Done** | | |
| Reliable sign recognition | **Blocked — DTW is a stub** | | |
| Unknown gate (both conditions) | **Done** (verified) | | |
| Thresholds calibrated | Not started | | |
| **Thresholds frozen before T4** | Not started | | |
| Urdu sentence templates | **Done** | | |
| P0 audio pre-generated | Placeholder tones only — needs Kokoro | | |
| Audio verified by ear | Not started | | |
| Confirm-before-speak | **Done** | | |
| Doctor phrase library | **Done** | | |
| Verified PSL playback | Not started | | |
| Unseen-person test (T4) | Not started | | |
| 9/10 rehearsal | Not started | | |
| Backup video | Not started | | |
| **Offline dry run (network disabled)** | Not started | | |

## Tier B — application shell (P1, cut second)

| Item | Status | Owner | Blocker |
|---|---|---|---|
| PostgreSQL schema + migrations | **Done** (verified) | | |
| Seed data loaded (all disabled) | **Done** | | |
| JSON snapshot export | **Done** (verified) | | |
| Staff login + roles | **Done** (verified) | | |
| Forgot password | **Done** | | |
| Session history + New Conversation | **Done** | | |
| Settings screen | **Done** | | |

## Tier C — admin console (P1/P2, cut first)

| Item | Status | Owner | Blocker |
|---|---|---|---|
| Dashboard (demo readiness, permission gaps) | **Done** | | |
| Signs management + verification workflow | **Done** (verified) | | |
| Messages management + audio staleness | **Done** (verified) | | |
| Doctor phrases management | **Done** | | |
| Testing records | **Done** | | |
| Assets and permissions | **Done** | | |
| User management | **Done** | | |
| Audit log | **Done** | | |

## Content and rights

| Item | Status | Owner | Blocker |
|---|---|---|---|
| **Pain-concept PSL verification (due end of Day 2)** | Not started | | |
| Permission request sent | Not started | | |
| Permission response received | Not started | | |
| Urdu wording reviewed by fluent speaker | Not started | | |
| Volunteer consent recorded per purpose | Not started | | |

## Counts

Report only `Reliable + Enabled`. Never quote experimental signs publicly.

```text
Reliable vocabulary:      0
Experimental vocabulary:  0
Demoable messages:        0
Demoable doctor phrases:  0
Demo-critical items not ready:  15 of 15
```

## Active recognition thresholds

```text
tau_accept:    not set
delta_margin:  not set
frozen:        no
```

## Known weak signs

- None recorded yet.

## Current top 3 risks

1. **Recognition is still a stub.** The application around it is complete and
   verified, but no sign has ever actually been recognised. Everything that
   matters now depends on landing MediaPipe + DTW and running the Day-1 trials.
2. **Pain-concept verification is unresolved** and gates the flagship message.
   The pain-free fallback set exists, so this is bounded.
3. **No audio is real yet.** The speech pipeline works end to end but plays
   placeholder tones until Kokoro is installed and a voice is chosen.

## Today's cut decision

`None` / admin console / application shell / English / history / skeleton / extra phrases / weak signs

## Next proof required

> Write exactly one measurable result here.

_Current: install MediaPipe, extract references for the five Day-1 signs, and
record a real number out of 100. The application is ready to receive it —
`/admin/testing` records the trials and calibrates the thresholds._
