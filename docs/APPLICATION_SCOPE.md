# Application Scope

PSL Bridge is now defined as a **proper application**, not only a hackathon demo. This document defines what that means, what is in each tier, and what must never be traded away to build it.

Supersedes the earlier "no login, no dashboard, no admin" position in [Product Spec](PRODUCT_SPEC.md) and [Requirements](REQUIREMENTS.md) — see D019 in the [Decision Log](DECISIONS_LOG.md).

## The governing distinction

> **The application may have login and admin pages. The PSL communication interface stays one clean, single-screen experience — and the patient never needs an account.**

Everything below follows from that sentence.

## Scope tiers

| Tier | Contents | Priority | Cut order |
|---|---|---|---|
| **A — Communication core** | camera, recognition, unknown gate, Urdu message, confirm-before-speak, Kokoro audio, doctor phrase playback | **P0** | never cut |
| **B — Application shell** | staff login, roles, session history, new conversation, settings, logout | **P1** | cut second |
| **C — Admin console** | dashboard, content CRUD, testing records, assets and permissions, user management, audit log | **P1 / P2** | cut first |

**The golden rule is unchanged.** When time slips, cut Tier C, then Tier B, then vocabulary and optional UI. Never cut unknown handling, confirm-before-speak, unseen-person testing, or the final reliability rehearsal.

Tiers B and C are real product work, but a polished admin console attached to an unreliable recogniser is a failed project. Tier A must be stable before Tier C is started.

## Access model

| User | Login required | Reason |
|---|---|---|
| **Patient** | **No** | A Deaf patient arriving in pain must not face account → email → password → OTP. Instant access is an accessibility and emergency-use requirement. |
| Doctor | Yes | identifies staff, enables audit |
| Nurse / Staff | Yes | same |
| Admin | Yes | manages content and users |

**No public signup.** There is no self-registration route. For a hospital product, accounts are created internally by an admin. This also removes an entire category of abuse and spam handling from the hackathon build.

### Roles and permissions

| Capability | Patient (anon) | Doctor | Staff | Admin |
|---|:--:|:--:|:--:|:--:|
| Use Patient → Doctor communication | ✔ | ✔ | ✔ | ✔ |
| Use Doctor → Patient phrase library | ✔ | ✔ | ✔ | ✔ |
| Doctor voice input (P1) | | ✔ | ✔ | ✔ |
| Start / clear a session | ✔ | ✔ | ✔ | ✔ |
| Change application settings | | | | ✔ |
| View admin dashboard | | | | ✔ |
| Edit signs / messages / phrases | | | | ✔ |
| Change verification or reliability status | | | | ✔ |
| Record test results | | ✔ | ✔ | ✔ |
| Manage assets and permissions | | | | ✔ |
| Manage users | | | | ✔ |
| View audit log | | | | ✔ |

The communication screen is reachable **without authentication** so a patient can always use it. Staff login adds identity, settings and admin access on top — it is not a gate in front of the camera.

### Login security

Baseline, no SSO for the hackathon:

- passwords hashed with Argon2id or bcrypt — never stored or logged in plaintext;
- short-lived access token plus a revocable refresh session, so logout and account deactivation take effect immediately;
- forgot-password via single-use, short-expiry token;
- `is_active = false` blocks login instantly without deleting history;
- role checked server-side on every admin endpoint — never only in the UI;
- failed logins recorded in the audit log.

## Routes

```text
/login                  staff login
/                       PSL communication screen  ← the one-screen experience
/settings               application settings (admin)
/admin                  dashboard
/admin/signs            signs and variants
/admin/messages         patient messages
/admin/doctor-phrases   doctor responses
/admin/testing          recognition test results
/admin/assets           videos, audio, permissions
/admin/users            staff accounts
```

Nine routes. `/` is the product; everything else supports it.

**The no-scroll rule applies to `/` only.** Admin tables scroll and paginate like any admin tool — forcing a data grid into one viewport would be pointless. [UI Spec](UI_SPEC.md) governs `/`; admin pages follow the same [Design System](DESIGN_SYSTEM.md) but are conventional.

## The communication screen

Unchanged from [UI Spec](UI_SPEC.md), plus a thin authenticated header when staff are logged in.

### Header
Brand · mode switch · signed-in staff name · **New Conversation** · logout.

When nobody is signed in, the header shows brand and mode switch only. The patient experience does not change based on login state.

### Patient → Doctor
Live camera · camera preview and framing guidance · detection status · recognised sign · Urdu meaning · current Urdu message · Speak · Undo · Retry · Clear · unknown-sign handling · Kokoro audio playback · optional landmark overlay.

### Doctor → Patient
Browse phrases by category · search · select phrase · play verified PSL video · replay · pause · full-screen · optional microphone input (P1).

Doctor phrase categories are defined in [Message Map](MESSAGE_MAP.md) §7: **Basic**, **Pain**, **Symptoms**, **Medical**.

## Session history

Shown during a consultation, so both sides can see what has been said:

```text
Patient   مجھے سینے میں درد ہے۔
Doctor    کب سے؟
Patient   دو دن سے۔
```

**Temporary by default. Cleared when the session ends.**

There is no `conversations` table. A consultation transcript is identifiable medical information; keeping it in memory only is both the simpler build and the stronger privacy position ([Data Model](DATA_MODEL.md), [Privacy, Ethics & Permissions](PRIVACY_ETHICS_PERMISSIONS.md)).

Persisting history later requires a retention policy, a consent flow and a fresh privacy review. It is not a small change and must not be added quietly.

### New Conversation

A single `+ New Conversation` button clears:

- recognised concepts,
- the current Urdu sentence,
- the session history,
- the selected doctor phrase.

The camera stays live. This is also the recovery action after a confusing exchange, so it must be reachable in one click at all times.

## Settings

| Setting | Values | Default |
|---|---|---|
| Primary output language | Urdu | Urdu |
| English text | on / off | off |
| Speech voice | selected Kokoro Hindi voice | set on Day 1 |
| English speech | on / off | off |
| Landmark overlay | on / off | off |
| Doctor voice input | on / off | off (P1) |
| STT provider | Groq / local / disabled | Groq |

Settings are admin-editable and stored in the `settings` table. Changing the voice marks pre-generated audio stale — see [Technology Stack](TECH_STACK.md) §5.

## Explicitly out of scope

| Item | Status |
|---|---|
| Patient accounts | Never — accessibility decision |
| Public signup | Never — accounts created internally |
| Patient medical records | Not for the hackathon |
| Stored consultation transcripts | Not by default; requires privacy review |
| Appointments, billing, hospital administration | Out of scope |
| Organisation hierarchy, multi-tenant | Out of scope for v1 |
| SSO | Out of scope for the hackathon |
| Full continuous PSL translation | Out of scope — [Roadmap](ROADMAP.md) Phase 2 |
| AI diagnosis or treatment advice | Never |
| Generated PSL avatar | Never in this scope |
| Unrestricted Urdu → PSL | Out of scope — voice only *selects* verified phrases |

## Build order

1. **Tier A end-to-end, ugly.** Camera → landmarks → DTW → unknown gate → Urdu → confirm → audio. No login, no styling.
2. **Doctor phrase playback.** Buttons plus verified video.
3. **Database + seed.** Content moves out of hardcoded lists into PostgreSQL, with the invariants enforced.
4. **Tier B shell.** Login, roles, session history, settings.
5. **Tier C admin.** Dashboard first, then signs, messages, phrases, testing, assets, users.
6. **Freeze, unseen-person test, rehearse.**

Steps 4 and 5 are only started once step 1 is stable on a second person. That ordering is the entire risk-management content of this document.
