# Offline & Fallback Strategy

## Goal

The core demo must survive poor venue internet. **The entire P0 demo runs with the network adapter disabled** — this is a verified QA step, not an assumption.

## Local by design

| Component | Local? |
|---|---|
| Camera | ✔ |
| MediaPipe Holistic tracking | ✔ |
| DTW recognition and unknown gate | ✔ |
| Controlled message construction | ✔ |
| Urdu text | ✔ |
| Urdu speech (pre-generated WAV) | ✔ |
| Doctor phrase selection | ✔ |
| Verified doctor PSL playback | ✔ (where permitted to bundle locally) |
| PostgreSQL | ✔ |
| Doctor voice input via Groq (P1) | ✖ — the only online component |

## Urdu speech

**Resolved by the stack freeze.** Urdu audio for every P0 message is generated with Kokoro **before the demo** and stored as local WAV files. There is no browser-voice dependency, no network call and no risk of a missing `ur-PK` voice on the demo laptop.

Fallback order:

```text
1. Pre-generated local WAV          ← P0 path
2. Live Kokoro generation, local    ← sentence with no pre-generated file
3. Urdu text only, no audio         ← never blocks the consultation
```

**Staleness is the real risk here, not availability.** If a message's Urdu text changes after its audio was generated, the screen and the speaker disagree. The `audio_source_checksum` guard blocks playback of stale audio, and regeneration is a pre-demo checklist item.

## Sentence construction

Deterministic local templates for every P0 message. **No cloud language service and no LLM are used in P0**, so there is nothing to fall back from.

## Database

PostgreSQL is a demo dependency, so it gets a fallback like everything else. The backend boots read-only from an exported snapshot:

```text
data/signs.json
data/messages.json
data/doctor_phrases.json
```

- Exported at feature freeze and re-exported after any content change.
- Filtered through the content invariants, so unverified or unpermitted content cannot leak into the fallback path.
- Snapshot mode is read-only — recognition, messages, audio and doctor playback work; admin editing and test recording do not.
- A **stale snapshot is dangerous**: it can restore a weak sign that was removed. Re-export after every content change and check the export timestamp before the demo.

## Doctor-side content

Use only permitted local assets. Do not copy third-party content without the needed permission. A phrase whose video lacks demo-playback permission cannot be enabled at all — the database enforces this.

## Doctor voice input (P1)

```text
Internet available   → Groq whisper-large-v3-turbo
Urdu accuracy poor   → Groq whisper-large-v3
No internet          → faster-whisper small, CPU int8
Both fail            → doctor clicks the phrase button
```

The manual buttons never leave the screen, so **speech recognition can never kill the demo**.

## Degraded-mode indicator

When the app is running on the snapshot, on live TTS, or on local STT, the header shows a small persistent indicator. Silent degradation during a judged demo is worse than a visible one.

## Backup demo video

Record a complete successful consultation on Day 5. Keep a local copy on the demo laptop and a second backup copy elsewhere.

During judging: attempt live first; if environment breaks the camera or recognition, openly use the backup recording.

## Hardware and environment checklist

- camera;
- speaker volume;
- browser permissions;
- screen scaling;
- charger and power;
- full-screen mode;
- notifications disabled;
- no pending restart or update;
- PostgreSQL service running, or a fresh snapshot present;
- `assets/audio/` populated and checksums current;
- `assets/psl-videos/` present for every enabled phrase;
- **full dry run with networking disabled**.
