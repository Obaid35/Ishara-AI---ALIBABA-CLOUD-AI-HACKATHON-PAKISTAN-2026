# Roadmap

## Phase 0 — Hackathon

- 15–30 reliable verified healthcare signs;
- Urdu text and pre-generated Urdu speech;
- two-condition unknown gate with frozen thresholds;
- patient confirmation before speech;
- 10–15 doctor PSL responses with categories;
- one-screen communication interface, no patient login;
- PostgreSQL content store with enforced invariants;
- staff login and admin console (Tier B/C, cut first if time slips);
- fully offline operation.

## Phase 1 — Stronger healthcare vocabulary

- 100+ verified medical concepts;
- more signers and measured signer diversity;
- stronger unseen-person testing across more people;
- regional variants as first-class supported entries;
- possible move from DTW to a temporal classifier **once the data justifies it**;
- hospital pilot feedback.

## Phase 2 — Continuous medical communication

### Segmentation without forced pauses

The current recogniser waits for the hands to stop: a capture ends only after
`K_END` consecutive frames below `THETA_END`, roughly 320 ms of stillness, then
a 600 ms refractory period. A deliberate signer produces those pauses. **A
fluent signer does not** — signs run into one another, so `below_count` never
reaches `K_END`, the capture runs to `T_MAX_MS` and aborts. Fluent signing is
therefore not supported today, and this is the single largest gap between what
the system does and what a Deaf patient actually signs.

The replacement is **sign spotting**, the technique behind wake-word detection:
stop asking "has the movement finished?" and start asking "is this sign present
anywhere in the last few seconds?"

- keep a rolling buffer of roughly the last 4 seconds of landmarks;
- every ~200 ms score the whole buffer against every reference;
- emit a sign when its distance dips below threshold, rather than when motion
  stops;
- suppress overlapping detections so one performance yields one decision (D027
  still holds).

**Half of this already exists.** `subsequence_distance()` scores with free start
and end on the query axis, so it already locates a reference *inside* a longer
capture. What is missing is the continuous scan, the suppression scheme, and
thresholds calibrated for it.

Deliberately **not** attempted during the hackathon build phase. Continuous
scanning multiplies the scoring cost, and a longer window gives far more chances
to match something by accident, so it needs its own thresholds and its own
validation — and that validation requires fluent signers, who were not available
to the project. Replacing a measured, working component with an untested one
before a deadline is the wrong trade.

**Entry condition:** fluent PSL signers available for recording and testing.
Without them this cannot be validated, only guessed at.

### Beyond segmentation

- multi-sign utterances;
- more natural PSL → Urdu;
- non-manual markers where linguistically required.

Note that even with all of this, continuous sign language translation remains an
open research problem for far better-resourced languages than PSL. Phase 2
widens what the system accepts; it does not turn it into an interpreter.

## Phase 3 — Doctor interaction

- Urdu speech mapped to a larger verified PSL phrase inventory;
- improved Urdu STT accuracy;
- interpreter escalation when a request is unsupported.

## Phase 4 — Deployment

- clinic kiosk;
- tablet/mobile;
- offline-first packaging;
- **privacy and security review before any deployment beyond a demo** — including a decision on whether consultation history may ever be stored, with retention and consent;
- proper secret management, not `.env` files;
- SSO or hospital identity integration;
- multi-site and role hierarchy if needed.

## Phase 5 — Additional domains

Separate verified packs for emergency services, government, banking, education, and customer service. Each pack repeats the same discipline: verified content, measured reliability, explicit limitations.

## What does not change with scale

- Unknown is better than confidently wrong.
- Nothing is spoken without the user's confirmation.
- The system never generates sign language.
- Only verified, permitted content reaches a user.
- Reported numbers carry their denominators.
- The patient never needs an account.

## Long-term rule

Expand only with Deaf-community participation, measured signer diversity, clear content rights, and transparent limitations.
