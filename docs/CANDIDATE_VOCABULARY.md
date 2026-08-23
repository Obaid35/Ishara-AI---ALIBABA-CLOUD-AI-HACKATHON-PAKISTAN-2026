# Candidate Healthcare Vocabulary

This is a **concept list**, not a claim that every item is one universal PSL sign. Every item must be verified.

Seeded into the `signs` table with `is_enabled = false`. Nothing here is in the product until it earns `Reliable + Enabled`.

## The 15-sign freeze list

Derived from the ten P0 messages plus the demo script — not chosen by convenience (D031). Full traceability: [Message Map](MESSAGE_MAP.md) §1.

| Sign | Serves | Demo critical |
|---|---|:---:|
| `HEADACHE` | message 1 | |
| `CHEST_PAIN` | message 2 | ✔ |
| `STOMACH_PAIN` | message 3 | |
| `FEVER` | message 4 | ✔ |
| `COUGH` | message 5 | |
| `VOMITING` | message 6 | |
| `DIZZINESS` | message 7 | |
| `BREATHING_PROBLEM` | message 8 | ✔ |
| `BLEEDING` | message 9 | |
| `HELP` | message 10 | |
| `YES` | demo answer | ✔ |
| `NO` | demo answer | ✔ |
| `TWO` | duration | ✔ |
| `DAY` | duration | ✔ |
| `INJURY` | message 11 / buffer | |

`DOCTOR` and `HOSPITAL` are **excluded** — visually distinct, but used by no P0 message. Verification and testing effort spent on them buys nothing demonstrable.

## Full candidate pool

Beyond the freeze list, for expansion only after the 15 are reliable.

### Basic
YES · NO · HELP · AGAIN · DOCTOR · HOSPITAL · MEDICINE · EMERGENCY

### Body/condition concepts
HEADACHE · EYE PAIN · CHEST PAIN · STOMACH PAIN · BACK PAIN · ARM PAIN · LEG PAIN · FOOT PAIN

> **All pain concepts are blocked on D015.** Do not assume a standalone `PAIN` sign or an English-style `HEAD + PAIN` composition. Verification is owned by the PSL/Data lead and due end of Day 2. A pain-free fallback message set exists (D024).

### Symptoms
FEVER · COUGH · VOMITING · NAUSEA · DIZZINESS · WEAKNESS · BREATHING PROBLEM · BLEEDING · SWELLING · INJURY · ALLERGY

### Time / quantity
TODAY · YESTERDAY · ONE · TWO · THREE · DAY · WEEK

### Severity/change
SEVERE · MILD / LITTLE · WORSE · BETTER

## Status lifecycle

```text
draft → psl_verified → testing → reliable → enabled
                          ↓
                     weak / dropped → disabled
```

Two independent columns: **verification status** (is the PSL correct?) and **reliability status** (does recognition work?). They are different questions with different reviewers. A sign can be perfectly verified PSL and still be technically weak — and it is then excluded.

Only `Reliable + Enabled` counts publicly.

## Finalization checklist per sign

- [ ] Verified PSL source
- [ ] Meaning reviewed by a signer/interpreter or trusted source
- [ ] `verified_by` and `verified_on` recorded
- [ ] Regional/variant concern noted
- [ ] Reference clip usable, with `extractor_version` recorded
- [ ] Rights status known for the source clip
- [ ] Live test completed on a **different person**
- [ ] Confusions checked, especially against its nearest neighbour
- [ ] No loosened threshold needed — stricter overrides only
- [ ] Reliable status earned
- [ ] Enabled, and dependent messages verified demoable
