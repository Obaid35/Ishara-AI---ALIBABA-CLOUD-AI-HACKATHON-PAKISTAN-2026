# Patient Medical Message Library

Judge the product by **useful medical messages**, not only sign count.

The authoritative mapping of concepts → Urdu → audio → demo step is [Message Map](MESSAGE_MAP.md). This file is the human-readable content list.

## P0 — ten messages

These ten are the P0 requirement. Each needs a reliable sign, a reviewed Urdu string, a `kokoro_input` line and pre-generated audio.

1. I have a headache. — *pain concept, blocked on D015*
2. I have chest pain. — *pain concept, blocked on D015*
3. My stomach hurts. — *pain concept, blocked on D015*
4. I have fever.
5. I have a cough.
6. I am vomiting.
7. I feel dizzy.
8. I am having difficulty breathing.
9. I am bleeding.
10. I need help.

## P1 — five more

11. My eye hurts.
12. My back hurts.
13. I feel weak.
14. I have an injury.
15. I have an allergy.

## Answer messages

- Yes. — `جی ہاں۔`
- No. — `جی نہیں۔`

Required by the demo script, so they are demo-critical despite being trivial.

## Pain-free fallback set

Three P0 messages depend on pain concepts whose PSL representation is unverified (D015). If verification does not complete by end of Day 2, the P0 ten becomes:

> fever · cough · vomiting · dizziness · weakness · difficulty breathing · bleeding · injury · allergy · need help

Ten messages, no pain concept, no reduction in scope. The demo's symptom step swaps `CHEST_PAIN` → `FEVER`. **The demo survives the pain concepts failing verification** (D024).

## Duration extensions

Where verified signs support them: today; yesterday; one/two/three days; one week.

**Bounded on purpose.** Composing duration into message text gives 15 symptoms × 4 durations = 60 messages, each needing its own reviewed Urdu, `kokoro_input` and WAV. Only the demo-critical combinations are pre-generated:

- `CHEST_PAIN + TWO + DAY`
- `FEVER + TWO + DAY`

Everything else falls back to the base message with the concepts shown.

## Severity extensions

mild/little; severe; worse; better. P1 — none are pre-generated for the demo.

## Urdu drafts

Review before final freeze. All strings pending review by a fluent Urdu speaker.

- `مجھے سر میں درد ہے۔`
- `میری آنکھ میں درد ہے۔`
- `مجھے سینے میں درد ہے۔`
- `میرے پیٹ میں درد ہے۔`
- `مجھے بخار ہے۔`
- `مجھے کھانسی ہے۔`
- `مجھے قے آ رہی ہے۔`
- `مجھے چکر آ رہے ہیں۔`
- `مجھے کمزوری محسوس ہو رہی ہے۔`
- `مجھے سانس لینے میں مشکل ہو رہی ہے۔`
- `مجھے خون آ رہا ہے۔`
- `مجھے مدد چاہیے۔`

## Each message carries

| Field | Purpose |
|---|---|
| `code` | stable identifier |
| concept sequence | ordered signs that produce it |
| `urdu_text` | shown on screen |
| `english_text` | optional toggle |
| `kokoro_input` | **Devanagari** pronunciation string for TTS |
| `audio_asset` | pre-generated WAV |
| `audio_source_checksum` | staleness guard |
| priority, demo-critical, enabled | scope and gating |

`kokoro_input` is never shown to a user. It exists because Kokoro's Hindi voices take Devanagari input, and it is verified **by ear**, not by reading it.

## P0 generation rule

Use known controlled patterns. **No LLM.** If a sequence is unsupported, show the recognised concepts and speak the base message rather than inventing a sentence.

## Enabling rule

A message can be enabled only when **every** sign in its sequence is `Reliable + Enabled`, and its audio checksum is current (invariants I1 and I3). Removing a weak sign automatically disables the messages that used it.
