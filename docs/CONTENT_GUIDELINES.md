# Content & Urdu Guidelines

## Tone

Simple, respectful, direct, and medically appropriate without unnecessary jargon.

## Suggested status wording

### Ready
- English: `Ready to sign`
- Urdu: `اشارہ کرنے کے لیے تیار`

### Reading
- English: `Reading sign…`
- Urdu: `اشارہ سمجھا جا رہا ہے…`

### Recognized
- English: `Recognized`
- Urdu: `اشارہ سمجھ لیا گیا`

### Repeat — ambiguous match
- English: `Please repeat the sign`
- Urdu: `براہِ کرم اشارہ دوبارہ کریں`

### Unknown — no match
- English: `Sign not recognized`
- Urdu: `اشارہ سمجھ نہیں آیا`

The two unknown states are worded differently on purpose. "Please repeat" means the system nearly had it; "not recognized" means it did not. Collapsing them into one message throws away information the patient can act on.

## Main actions

Speak to Doctor · Undo · Clear · Try Again · Play PSL · Replay · Back to Patient · New Conversation

## Medical wording rules

- translate supported meaning only;
- never add diagnosis;
- never invent severity or duration;
- never change yes/no;
- never add an unrecognized body part.

## Sentence style

Prefer natural Urdu instead of literal word order.

Example: `CHEST_PAIN + TWO + DAY` → `مجھے دو دن سے سینے میں درد ہے۔`

Final Urdu must be checked by a fluent Urdu speaker. PSL meaning must be checked independently through a knowledgeable signer/interpreter or verified resource.

## Authoring `kokoro_input`

Every message carries a second text field that users never see: the **Devanagari** pronunciation string passed to Kokoro's Hindi voices.

| Field | Example | Shown to user |
|---|---|:--:|
| `urdu_text` | `مجھے سینے میں درد ہے۔` | ✔ |
| `kokoro_input` | `मुझे सीने में दर्द है।` | ✖ |

Rules:

1. `kokoro_input` is a **pronunciation aid, not a translation.** It transcribes how the Urdu sentence should sound, not how a Hindi speaker would phrase it.
2. It is authored by hand for each message.
3. It is **verified by ear** — an Urdu speaker listens to the generated audio and judges whether it sounds right. It is never verified by reading the Devanagari, because reading it correctly is a different skill from hearing whether the output is natural.
4. Prefer everyday spoken forms over formal or Sanskritised vocabulary; the goal is natural spoken Urdu, not correct written Hindi.
5. Medical terms are the risk area. Check each one individually.

### Staleness

Changing `urdu_text` or `kokoro_input` **invalidates the generated audio**. The checksum guard blocks playback and the admin console shows a stale-audio warning.

A screen that reads one sentence while the speaker says another is a medical-safety failure, not a cosmetic bug. Never ship an edit without regenerating.

## Doctor-side wording

Doctor phrase labels are for the doctor, in Urdu and English. The patient sees only the verified PSL video — so a label may be rephrased freely, but **the video may never be swapped without re-verification**.

## Words to avoid in the product and the pitch

| Do not say | Say instead |
|---|---|
| "translates PSL" | "communicates a verified healthcare vocabulary" |
| "AI understands sign language" | "recognizes verified signs; refuses when uncertain" |
| "Kokoro supports Urdu" | "Kokoro Hindi voices, used for Urdu-like speech" |
| "diagnoses" / "detects illness" | "communicates what the patient signed" |
| a bare accuracy percentage | the number **with its denominator and population** |
