# Doctor → Patient Response Library

## Principle

Doctor-side communication uses a **small verified phrase library**. The product does not attempt unrestricted Urdu speech → generated PSL.

Full table with codes, Urdu strings and demo flags: [Message Map](MESSAGE_MAP.md) §7.

## Categories

Phrases are grouped so the doctor side is fast to operate:

**Basic** — Do you understand? · Please wait here.
**Pain** — Where is the pain? · Since when? · Is the pain severe?
**Symptoms** — Fever? · Cough? · Vomiting? · Dizzy? · Difficulty breathing?
**Medical** — Allergy to medicine? · Taken any medicine? · Injury? · We need a test. · Take this medicine.

## P0 — ten phrases

The first ten across Basic, Pain and Symptoms are P0. The five Medical phrases are P1.

Two are demo-critical: **Since when?** and **Difficulty breathing?**

## Verification rule

Every doctor phrase requires:

- verified PSL representation;
- permission/right to display its video;
- clear playback;
- clear Urdu/English label for the doctor.

A phrase can be enabled only when it is `psl_verified` **and** its video has `permitted_demo_playback = true` (invariant I2). Both conditions are shown as a checklist in the admin console, so a blocked enable explains itself.

## Do not use

Do not let unqualified team members improvise medical PSL and present it as correct. If a phrase cannot be verified, **remove it** (D013).

## Playback controls

Play · Pause · Replay · Full-screen · Back.

## Doctor voice input — P1

The doctor may speak Urdu instead of clicking. The transcription is matched against `stt_aliases` on this fixed list; the matched phrase is **shown for confirmation**; then the verified video plays.

- Speech only *selects* an existing verified phrase. **The system never generates PSL.**
- Below the match threshold, nothing plays — the doctor uses the buttons.
- Confirm-before-play mirrors confirm-before-speak on the patient side (D029). A misheard question must not silently play the wrong verified video.
- The buttons never leave the screen, so STT can never break the demo.

## Each phrase carries

| Field | Purpose |
|---|---|
| `code` | stable identifier |
| `category` | Basic / Pain / Symptoms / Medical |
| `urdu_text`, `english_text` | doctor-facing label |
| `psl_asset` | verified PSL video |
| `verification_status`, `verified_by`, `verified_on` | who verified the PSL, and when |
| permission status | from the asset's rights record |
| `stt_aliases` | spoken phrasings that map here |
| priority, demo-critical, enabled, sort order | scope and layout |
