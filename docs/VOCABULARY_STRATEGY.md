# Vocabulary Strategy

## Main rule

Do not design PSL vocabulary by translating English words one-by-one. PSL has its own structure and regional variation.

The project uses **verified supported concepts**, not a claim that every English/Urdu word maps to one universal PSL sign.

## Target

- First: 15 rock-solid signs — the freeze list in [Candidate Vocabulary](CANDIDATE_VOCABULARY.md).
- Then: 20 → 25 → 30 only after testing.
- Stretch: 30–40 reliable signs.

The 15 are **derived from the P0 messages and the demo script**, not picked for convenience (D031). Every sign must earn its place by being needed by something the product actually does.

## Entry criteria

A sign enters the demo vocabulary only if:

1. medically useful;
2. PSL meaning verified, with `verified_by` and `verified_on` recorded;
3. source/recording is legitimate and its rights are known;
4. live testing on a **different person** is acceptable;
5. dangerous confusions are understood and documented;
6. it passes the unknown gate **without a loosened threshold**.

Criterion 6 is how weak signs are kept out. A sign that only works when the gate is relaxed is Weak and is removed (D028).

## Pain/body-part rule

Do **not** assume `HEAD + PAIN` is the correct PSL construction. Concepts may instead be HEADACHE, EYE PAIN, CHEST PAIN, BACK PAIN, STOMACH PAIN, etc. The actual PSL representation must be verified before finalizing (D015).

**Owned by the PSL/Data lead, due end of Day 2.** It gates three signs and the flagship message. A pain-free fallback P0 set exists so the demo is not hostage to the answer (D024).

## High-risk confusions

Extra testing for:

- YES vs NO;
- mild vs severe;
- one/two/three;
- body-location signs;
- breathing problem;
- allergy;
- bleeding;
- emergency/help.

YES and NO are tested on **Day 1**, deliberately. If the highest-risk pair cannot be separated, the team needs that answer immediately, not on Day 5.

A sign in this list may carry a **stricter** per-sign margin override. Never a looser one.

## Statuses

Two independent axes, stored separately in the `signs` table:

**Verification** — is the PSL correct?
`draft` → `psl_verified` → (or `rejected`)

**Reliability** — does recognition work?
`candidate` → `experimenting` → `testing` → `reliable` → (or `weak` / `dropped`)

Plus `is_enabled` — is it live in the product?

Only **`Reliable + Enabled`** signs are included in the final verified count and in anything quoted publicly (D009).

## Removal has consequences

Setting a sign to `weak` or `dropped` **automatically disables every message that depends on it** (invariant I1). The admin console shows exactly which messages will be affected before confirming.

This exists because the alternative — discovering the dependency by watching a demo step fail during rehearsal — is the failure mode that costs a hackathon its demo.
