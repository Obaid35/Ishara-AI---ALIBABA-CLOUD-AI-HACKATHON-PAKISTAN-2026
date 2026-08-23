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

- better segmentation without forced pauses;
- multi-sign utterances;
- more natural PSL → Urdu;
- non-manual markers where linguistically required.

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
