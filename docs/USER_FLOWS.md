# User Flows

# Patient → Doctor

```text
Open app  (no login required)
  ↓
Patient → Doctor selected
  ↓
Camera ready
  ↓
Patient signs
  ↓
System waits for complete sign movement
  ↓
Unknown gate
 ├─ No match      → “Sign not recognized” → sign again
 ├─ Ambiguous     → “Please repeat”       → sign again
 └─ Recognized    → show concept + Urdu
                        ↓
                  Add to message
                        ↓
                  More signs?
                   ├─ Yes → continue
                   └─ No  → build controlled Urdu sentence
                              ↓
                        Patient reviews
                              ↓
                        Correct?
                         ├─ No  → Undo / Clear / Retry
                         └─ Yes → Speak to Doctor
                                    ↓
                              Local audio plays
```

# Doctor → Patient

```text
Switch mode
  ↓
Phrases shown by category  (Basic / Pain / Symptoms / Medical)
  ↓
Doctor selects — button or search
  ↓
Verified PSL video opens
  ↓
Patient watches / replays / full-screen
  ↓
Choose another phrase or return
```

## Doctor voice input — P1

```text
Doctor presses microphone
  ↓
Speaks Urdu
  ↓
STT  (Groq → local → unavailable)
  ↓
Match against approved phrase list
  ↓
Confident match?
 ├─ No  → nothing plays → doctor uses buttons
 └─ Yes → show matched phrase
             ↓
        Doctor confirms
             ↓
        Verified PSL video plays
```

The system never generates PSL. Speech only selects an existing verified phrase, and the doctor confirms before it plays.

# Unknown sign

```text
Movement
  ↓
Not sufficiently certain — poor match, or too close to a rival sign
  ↓
Do NOT guess
  ↓
Show “Please repeat” or “Not recognized”
  ↓
No word added, no speech
```

# Wrong recognized sign

```text
Recognized result appears
  ↓
Patient sees mismatch
  ↓
Undo / Retry
  ↓
Incorrect concept removed
```

# New conversation

```text
+ New Conversation
  ↓
Clears recognized concepts, current sentence,
session history, selected doctor phrase
  ↓
Camera stays live
```

Available at all times in one click — it is also the recovery action after a confusing exchange.

# Staff login — P1

```text
/login
  ↓
Email + password
  ↓
Valid and account active?
 ├─ No  → error, attempt recorded in audit log
 └─ Yes → land directly on the communication screen
             ↓
      Admin role also unlocks /admin and /settings
```

There is no signup route. Accounts are created by an admin.

**Login never gates the communication screen.** A patient reaching an unattended laptop can always sign.

# Degraded operation

```text
Database unreachable      → read-only JSON snapshot + indicator
Pre-generated audio absent → live Kokoro → text only
Groq unavailable          → local STT → phrase buttons
Camera or recognition dead → backup demo recording
```

**Design principle:** the Deaf patient must visually control what the system communicates aloud — and no single failure may stop the consultation.
