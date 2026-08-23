# Risk Register

## Recognition and data

| Risk | Impact | Early warning | Mitigation |
|---|---|---|---|
| Dictionary example does not generalize | Critical | Source works, live person fails | Day-1 100-trial test; targeted recordings |
| Wrong/unverified PSL | Critical | Team interpretations differ | Deaf signer/interpreter review; remove uncertain signs |
| Wrong sign is spoken | Critical | Forced predictions | Two-condition unknown gate + confirm-before-speak |
| Pain concepts unverifiable | High | D015 unresolved past Day 2 | Pain-free fallback P0 message set (D024); demo swaps to `FEVER` |
| Sign completion poor | High | Duplicate/early outputs | Motion-energy segmentation with hysteresis; one motion → one decision |
| YES/NO not separable | High | Confusion pair in Day-1 data | Both tested on Day 1 specifically so failure is known early |
| Vocabulary too large | High | Confusion rises | Freeze 15 reliable first |
| Camera/lighting changes | High | Venue result lower | Normal-room tests + backup demo |
| Regional variation | Medium/High | New signer uses another variant | State supported verified variants; variants are first-class rows |
| Thresholds tuned on the unseen person | High | T4 run after a threshold change | Freeze thresholds before T4; changing them voids the result (D026) |

## Engineering

| Risk | Impact | Early warning | Mitigation |
|---|---|---|---|
| Frame streaming to Python too slow | High | Day-1 latency measurement poor | Pre-approved contingency: move extraction to browser MediaPipe Tasks (D035) |
| Extractor version mismatch between references and live | Critical | Distances look wrong with no error | `extractor_version` recorded per reference; stale references flagged |
| Kokoro Hindi G2P dependency missing | High | TTS fails on first run | Install and verify the Hindi path on **Day 1**, not Day 4 |
| Kokoro Hindi pronunciation poor for Urdu | Medium/High | Urdu speakers find it unnatural | Blind listening test across all four voices on Day 1; verified by ear per message |
| Audio stale after text edit | **Critical** | Screen and speaker disagree | `audio_source_checksum` blocks playback; regeneration is a checklist item |
| PostgreSQL unavailable at demo | High | Service not running | Read-only JSON snapshot boot (D021) |
| Stale snapshot restores removed content | High | Weak sign reappears mid-demo | Re-export after every content change; timestamp shown on dashboard |
| Venue internet fails | Medium | Cloud intermittency | Only P1 STT needs network; buttons always available |
| Credential committed to the repo | High | `.env` tracked | `.env` gitignored; `.env.example` placeholders only; no credential in docs |
| Weak sign removed but its message still enabled | High | Demo step fails in rehearsal | Invariant I1 cascade disables dependent messages automatically |

## Scope and schedule

| Risk | Impact | Early warning | Mitigation |
|---|---|---|---|
| **Admin/auth work displaces recognition work** | **Critical** | Login screen exists before a second person has been tested | Tier A must be stable first (D036); Tier C is cut first |
| Feature creep | High | New features during rehearsal | Freeze; cut admin, then shell, then vocabulary — never testing |
| UI consumes build time | Medium | Recognition unstable by Day 3 | Ugly end-to-end first |
| Planning outweighs building | Medium/High | Documentation grows while no code runs | Day-1 exit gate is a measured result, not a document |
| Volunteers unavailable | High | Recording delayed | Recruit before Day-1 result |
| Day 5 overloaded | Medium | Freeze and rehearsal collide | Freeze at end of Day 5; rehearse Day 6 |

## Content, rights and safety

| Risk | Impact | Early warning | Mitigation |
|---|---|---|---|
| Third-party video permission unclear | High | No explicit reuse permission | Request permission Day 1; separate viewing from redistribution; I2 blocks enabling |
| Doctor response is inaccurate | Critical | Unverified team-created phrase | Verified content only or remove the phrase (D013) |
| Doctor voice input selects the wrong phrase | High | Misheard Urdu | Confirm-before-play (D029); reject below match threshold |
| Volunteer consent assumed rather than recorded | High | Recording used for a purpose not granted | Per-purpose consent rows; invariant I8 |
| Consultation transcript stored by accident | High | A `conversations` table appears | History is in memory only (D033); adding storage requires privacy review |
| Medical overclaim | High | Pitch says "diagnose" | Communication-only language |
| Claiming Urdu TTS support | Medium | "Kokoro supports Urdu" in the pitch | Disclosed as Hindi voices used for Urdu-like speech (D023) |
| Inflated sign count quoted | Medium | Experimental signs included | Only `v_production_vocabulary` is quoted publicly |

## The two risks to watch this week

1. **Admin/auth displacing recognition work.** The scope just grew by an admin console, authentication and a database. The recognition core is still unproven. If the login screen exists before an unseen person has signed successfully, the project is failing.
2. **Pain-concept verification.** Three signs, the flagship message and half the message library depend on it. Owned, due end of Day 2, with a pre-planned fallback.
