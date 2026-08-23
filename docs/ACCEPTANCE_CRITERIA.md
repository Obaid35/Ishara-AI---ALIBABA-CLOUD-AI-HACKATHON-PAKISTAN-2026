# Acceptance Criteria

The prototype is demo-ready only when all P0 criteria pass. P0 is Tier A plus the engineering criteria below; the application shell and admin console are not demo blockers.

## Patient → Doctor
- [ ] Live camera works.
- [ ] The communication screen is usable **with no login**.
- [ ] At least 15 signs are `Reliable + Enabled`.
- [ ] At least 10 medical messages work.
- [ ] Urdu message appears correctly.
- [ ] Urdu speech works from pre-generated local audio.
- [ ] Recognition is visible before speech.
- [ ] Speak is manually triggered.
- [ ] Undo/Clear/Retry work.
- [ ] Unknown state works for both conditions — no match and ambiguous.
- [ ] One completed motion produces at most one decision.
- [ ] At least one unseen signer tested.

## Doctor → Patient
- [ ] At least 10 doctor phrases.
- [ ] Each demo phrase has verified PSL.
- [ ] Rights/permission documented for every displayed video.
- [ ] Video play/replay works.
- [ ] If voice input is enabled, the matched phrase is confirmed before the video plays.

## Engineering
- [ ] Every demo-critical sign, message and phrase appears in `v_demo_readiness` as ready.
- [ ] Recognition thresholds calibrated and **frozen before the unseen-person test**.
- [ ] Audio checksums current — no message has stale audio.
- [ ] JSON snapshot exported and dated after the last content change.
- [ ] Application boots and demos correctly with PostgreSQL stopped.
- [ ] **Full demo completes with the network adapter disabled.**
- [ ] No credential in any committed file; `.env` is gitignored.

## Safety
- [ ] No diagnosis.
- [ ] No treatment recommendation.
- [ ] No forced guess.
- [ ] Nothing spoken without explicit patient confirmation.
- [ ] No patient account, patient record or stored transcript exists.
- [ ] Limitation statement available.

## Reliability
- [ ] Exact demo rehearsed 10 times.
- [ ] 9/10 succeed without developer intervention.
- [ ] Backup demo recording exists locally, plus a second copy.

## Honest presentation
- [ ] Reliable sign count reported accurately from `v_production_vocabulary`.
- [ ] Weak signs excluded from the verified count.
- [ ] Unknown and wrong reported as separate numbers, each with its denominator.
- [ ] Existing-video limitations disclosed.
- [ ] Regional-variation limitation disclosed.
- [ ] Urdu speech disclosed as Kokoro **Hindi** voices, not an Urdu TTS model.
- [ ] Number of people tested and the unseen-person result stated.
