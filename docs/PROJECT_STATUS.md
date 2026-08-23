# Project Status

Use this file as the daily truth source. Fill it in — an unfilled status file is worse than none, because it looks like information.

## Current stage

`Planning` / Day 1 / Day 2 / Day 3 / Day 4 / Day 5 / Day 6 / Demo Ready

**Last updated:** 2026-08-23
**Updated by:** _(name)_

## Tier A — communication core (P0, never cut)

| Item | Status | Owner | Blocker |
|---|---|---|---|
| Stack installed and running end-to-end | Not started | | |
| Kokoro Hindi install verified | Not started | | |
| Kokoro voice chosen by blind test | Not started | | |
| 5-sign Day-1 experiment | Not started | | |
| 100 live trials | Not started | | |
| Data strategy decision | Not started | | |
| Frame-latency measurement recorded | Not started | | |
| Patient live camera | Not started | | |
| Sign segmentation (one motion → one decision) | Not started | | |
| Reliable sign recognition | Not started | | |
| Unknown gate (both conditions) | Not started | | |
| Thresholds calibrated | Not started | | |
| **Thresholds frozen before T4** | Not started | | |
| Urdu sentence templates | Not started | | |
| P0 audio pre-generated | Not started | | |
| Audio verified by ear | Not started | | |
| Confirm-before-speak | Not started | | |
| Doctor phrase library | Not started | | |
| Verified PSL playback | Not started | | |
| Unseen-person test (T4) | Not started | | |
| 9/10 rehearsal | Not started | | |
| Backup video | Not started | | |
| **Offline dry run (network disabled)** | Not started | | |

## Tier B — application shell (P1, cut second)

| Item | Status | Owner | Blocker |
|---|---|---|---|
| PostgreSQL schema + migrations | Not started | | |
| Seed data loaded (all disabled) | Not started | | |
| JSON snapshot export | Not started | | |
| Staff login + roles | Not started | | |
| Forgot password | Not started | | |
| Session history + New Conversation | Not started | | |
| Settings screen | Not started | | |

## Tier C — admin console (P1/P2, cut first)

| Item | Status | Owner | Blocker |
|---|---|---|---|
| Dashboard (demo readiness, permission gaps) | Not started | | |
| Signs management + verification workflow | Not started | | |
| Messages management + audio staleness | Not started | | |
| Doctor phrases management | Not started | | |
| Testing records | Not started | | |
| Assets and permissions | Not started | | |
| User management | Not started | | |
| Audit log | Not started | | |

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

1. Recognition core is unproven while scope has grown to include auth, admin and a database.
2. Pain-concept verification is unresolved and gates the flagship message.
3. Nothing has been measured yet — the Day-1 exit gate has not been run.

## Today's cut decision

`None` / admin console / application shell / English / history / skeleton / extra phrases / weak signs

## Next proof required

> Write exactly one measurable result here.

_Current: run the Day-1 experiment and record a real number out of 100._
