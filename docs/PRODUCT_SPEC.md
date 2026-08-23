# Product Specification

## Summary

Ishara AI is a healthcare communication application. Its centre is a **one-screen communication interface** with two modes:

1. **Patient → Doctor**
2. **Doctor → Patient**

Around that centre sits a small application shell — staff login, settings, and an admin console for managing verified medical content. Scope tiers, roles and routes are defined in [Application Scope](APPLICATION_SCOPE.md).

> **The patient never needs an account.** No login, no signup, no OTP. A Deaf patient opens the communication screen and starts signing.

There are no patient records, no appointments and no hospital-management workflow.

# Mode A — Patient → Doctor

## Goal

Convert a supported live PSL sign sequence into a short Urdu medical message and speak it aloud **only after patient confirmation**.

## Flow

1. Patient opens Patient → Doctor mode.
2. Camera becomes ready.
3. Patient performs a supported sign.
4. System waits for the complete sign movement.
5. System returns recognized, uncertain/repeat, or unknown.
6. Recognized sign appears visually.
7. Patient can continue signing.
8. Supported concepts become a controlled Urdu sentence.
9. Patient reviews it.
10. Patient presses **Speak to Doctor**.
11. Urdu voice plays from a pre-generated local audio file.
12. Undo, Clear, and Retry remain available.

## Confirm-before-speak

The app must **never automatically speak every detected movement**. Speech happens only after an explicit patient action. This holds regardless of how confident recognition is.

## Unknown-sign rule

The app must be allowed to say: **"Sign not recognized — please repeat."** It must not force every movement into a supported class. The gate is specified in [Recognition Specification](RECOGNITION_SPEC.md) §4.

## Message construction

Use controlled message patterns only — a recognized concept sequence maps to a pre-written, reviewed Urdu string. **No LLM is used in P0.** Do not assume PSL grammar equals Urdu grammar. Examples only after PSL meaning is verified:

- `HEADACHE` → `مجھے سر میں درد ہے۔`
- `CHEST_PAIN` → `مجھے سینے میں درد ہے۔`
- `BREATHING_PROBLEM` → `مجھے سانس لینے میں مشکل ہو رہی ہے۔`

If a signed sequence has no template, show the recognized concepts and speak the base message — never invent a sentence. Full mapping: [Message Map](MESSAGE_MAP.md).

## Urdu speech

Audio for the P0 message set is **pre-generated locally with Kokoro before the demo** and played from disk. No network call, no generation delay, no missing-voice failure. Live generation exists only as a fallback for a sentence with no pre-generated file. See [Technology Stack](TECH_STACK.md) §5.

# Mode B — Doctor → Patient

## Goal

Allow staff to communicate a limited set of common medical questions/messages to the patient.

## Flow

1. Doctor switches mode.
2. Verified phrases appear, grouped by category — Basic, Pain, Symptoms, Medical — with search.
3. Doctor selects one.
4. Corresponding **verified PSL video** opens.
5. Patient watches; Play/Pause/Replay/Full-screen available.

## Doctor voice input — P1

The doctor may optionally press a microphone and speak Urdu. The transcription is **matched against the existing approved phrase list**, the matched phrase is shown for confirmation, and then the verified PSL video plays.

Speech only *selects* one of our verified questions. **The system never generates PSL.** If nothing matches confidently, no video plays and the doctor uses the buttons.

## Boundary

The product does not attempt unrestricted doctor speech → generated PSL. Fixed verified content is safer and more achievable.

# Session history

During a consultation, both sides can see what has been said. **History is temporary and cleared when the session ends** — there is no stored transcript. `+ New Conversation` clears the recognized concepts, current sentence, history and selected phrase while keeping the camera live.

# One-screen requirement

For the communication screen on the hackathon laptop:

- no page scroll;
- no sidebar;
- no nested navigation;
- no patient account flow.

Admin pages are conventional data screens and may scroll and paginate. The no-scroll rule applies to `/` only.

# Language

Primary: Urdu text + Urdu speech. English text and English speech are optional toggles after P0 stability, using the same TTS system.

# Medical safety

The product translates and communicates supported meaning only. It must not diagnose, infer disease, recommend medicine, or generate treatment advice.
