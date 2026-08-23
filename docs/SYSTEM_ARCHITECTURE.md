# System Architecture

High-level architecture. Concrete technology choices are frozen in [Technology Stack](TECH_STACK.md); recognition parameters are in [Recognition Specification](RECOGNITION_SPEC.md).

## Patient → Doctor data flow

```text
LIVE CAMERA                          browser, getUserMedia
   ↓                                 frames over localhost WebSocket
Hand / body / face motion            MediaPipe Holistic (Python)
   ↓                                 normalised to shoulder-width units
Complete-sign detection              motion-energy start/end + hysteresis
   ↓
Sign recognition                     DTW against verified reference clips
   ↓
Unknown / confidence gate            τ_accept AND different-label margin
   ↓
Supported concept
   ↓
Controlled Urdu message builder      local template lookup — no LLM
   ↓
Patient confirmation                 explicit action, always required
   ↓
Urdu speech                          pre-generated local WAV (Kokoro)
```

## Doctor → Patient data flow

```text
Doctor selects verified phrase       buttons, grouped by category
   ↓
Phrase lookup                        PostgreSQL / JSON snapshot
   ↓
Verified PSL video                   local asset, permission-checked
   ↓
Patient watches / replays
```

Optional P1 voice path:

```text
Doctor speaks Urdu
   ↓
STT                                  Groq whisper-large-v3-turbo → local fallback
   ↓
Match against approved phrase list   closed set, never generative
   ↓
Doctor confirms the matched phrase
   ↓
Verified PSL video
```

## Components

### 1. Camera Capture
Live video from the device via the browser. Nothing is recorded or uploaded.

### 2. Motion Representation
MediaPipe Holistic landmarks, reduced to a 98-dimension per-frame vector, translated to the shoulder midpoint and scaled by shoulder width. Keeps the movement information needed for recognition rather than relying on clothing, background or body size.

### 3. Sign Completion
Waits for a full sign movement rather than outputting a label on every frame. One completed motion produces **at most one** decision.

### 4. Sign Recognition
DTW against verified reference clips, length-normalised so thresholds are comparable across the vocabulary. Reference clips and live input must be processed by the **identical** extraction path.

### 5. Unknown Gate
Two independent conditions — absolute match quality, and separation from the best *different-label* candidate. Prevents forced guesses. Tuned to keep wrong-accepts ≤ 2% even at the cost of a ~20% retry rate.

### 6. Message Builder
Maps a recognized concept sequence to a pre-written, reviewed Urdu string. Deterministic lookup, no generation. Unsupported sequences display concepts rather than inventing a sentence.

### 7. Urdu Speech
Plays a pre-generated local WAV, only after patient confirmation. Live TTS is a fallback path.

### 8. Doctor Phrase Library
Maps fixed doctor selections to verified PSL videos, gated on verification status and demo permission.

### 9. Content Store
PostgreSQL holds signs, messages, phrases, assets, rights, participants, consent, test results, users, settings and audit logs. Media files stay on disk; the database stores paths and checksums.

### 10. Application Shell
Staff authentication, roles, settings and the admin console. Sits around the communication core and is never a prerequisite for patient use.

## Architecture boundaries

- **The main demo does not depend on venue internet.** Only optional doctor voice input reaches the network, and it degrades to local STT and then to manual buttons.
- **Patient video is never permanently stored.** Frames and landmarks are processed in memory and discarded. There is no patient table and no session storage.
- **Unknown handling is a core system behavior**, not merely a UI label.
- **Content safety is enforced at the data layer**, so a rushed change cannot put unverified content in front of a patient.
- **No single dependency can kill the demo.** Database → JSON snapshot. Groq → local STT → buttons. Live TTS → pre-generated audio. Live demo → backup recording.
