# Message Map — Sign → Message → Demo Traceability

This document answers a question no other document previously answered: **exactly which signs must be `Reliable` for the P0 messages and the demo script to work.**

Without it, the vocabulary can be frozen on Day 6 without the demo's own signs being in the reliable set. Stored form: [Data Model](DATA_MODEL.md). Recognition behaviour: [Recognition Spec](RECOGNITION_SPEC.md).

## The chain

```text
sign (Reliable + Enabled)
  → message_concepts (ordered sequence)
    → patient_message (urdu_text + kokoro_input)
      → assets/audio/*.wav (pre-generated)
        → demo script step
```

A break anywhere in that chain means a demo step fails. Invariant I1 in the data model enforces the first link; this document is where the team can see the whole chain on one page.

## 1. The 15-sign freeze list

Derived from the ten P0 patient messages plus the four signs the demo script needs. This is the working target, not a claim — every entry still has to earn `Reliable` through testing.

| # | Sign code | Serves | Demo critical | Verification risk |
|---:|---|---|:---:|---|
| 1 | `HEADACHE` | message 1 | | **Pain concept — D015** |
| 2 | `CHEST_PAIN` | message 2 | ✔ | **Pain concept — D015** |
| 3 | `STOMACH_PAIN` | message 3 | | **Pain concept — D015** |
| 4 | `FEVER` | message 4 | ✔ | low |
| 5 | `COUGH` | message 5 | | low |
| 6 | `VOMITING` | message 6 | | low |
| 7 | `DIZZINESS` | message 7 | | low |
| 8 | `BREATHING_PROBLEM` | message 8 | ✔ | medium — high-risk confusion |
| 9 | `BLEEDING` | message 9 | | medium — high-risk confusion |
| 10 | `HELP` | message 10 | | low |
| 11 | `YES` | demo answer | ✔ | **high — YES/NO confusion** |
| 12 | `NO` | demo answer | ✔ | **high — YES/NO confusion** |
| 13 | `TWO` | duration | ✔ | medium — one/two/three confusion |
| 14 | `DAY` | duration | ✔ | low |
| 15 | `INJURY` | message 11 / buffer | | low |

**Seven of the fifteen are demo-critical.** If any of those seven fails to reach `Reliable`, the demo script changes — not the standard.

`DOCTOR` and `HOSPITAL` are deliberately **not** on this list. They appear in no P0 message and would consume verification and testing effort that buys nothing demonstrable.

## 2. Pain concepts are the critical path

Three of the fifteen signs, and the flagship message used throughout [Product Spec](PRODUCT_SPEC.md) and [UI Spec](UI_SPEC.md), depend on a linguistic question this project has explicitly recorded as unresolved:

> D015 — do not assume a universal standalone `PAIN` sign or an English-style `HEAD + PAIN` composition.

**Owner and deadline required.** PSL verification of the pain concepts must be assigned to the PSL/Data lead and resolved by **end of Day 2**. It is not a Day-5 discovery.

### Pain-free fallback message set

If pain concepts cannot be verified in time, the P0 set does **not** shrink. Messages 6–15 of the [Patient Medical Message Library](MEDICAL_MESSAGE_LIBRARY.md) contain no pain concept at all, and give a complete alternative ten:

| Fallback P0 messages | Signs required |
|---|---|
| fever, cough, vomiting, dizziness, weakness, breathing difficulty, bleeding, injury, allergy, need help | `FEVER` `COUGH` `VOMITING` `DIZZINESS` `WEAKNESS` `BREATHING_PROBLEM` `BLEEDING` `INJURY` `ALLERGY` `HELP` |

Plus `YES` `NO` `TWO` `DAY` for the demo = 14 signs, one spare.

The demo's symptom step then uses `FEVER` instead of `CHEST_PAIN`, which is why `FEVER` is marked demo-critical alongside `CHEST_PAIN`. **The demo survives the pain concepts failing verification.** That is a deliberate design property, not luck.

## 3. P0 patient messages

Ten messages are P0. The remaining five from the library are P1. This split did not previously exist anywhere — both libraries listed fifteen while the requirement was ten.

| # | Code | Concepts | Urdu | Audio file | P |
|---:|---|---|---|---|:--:|
| 1 | `HEADACHE` | `HEADACHE` | مجھے سر میں درد ہے۔ | `headache.wav` | P0 |
| 2 | `CHEST_PAIN` | `CHEST_PAIN` | مجھے سینے میں درد ہے۔ | `chest_pain.wav` | P0 |
| 3 | `STOMACH_PAIN` | `STOMACH_PAIN` | میرے پیٹ میں درد ہے۔ | `stomach_pain.wav` | P0 |
| 4 | `FEVER` | `FEVER` | مجھے بخار ہے۔ | `fever.wav` | P0 |
| 5 | `COUGH` | `COUGH` | مجھے کھانسی ہے۔ | `cough.wav` | P0 |
| 6 | `VOMITING` | `VOMITING` | مجھے قے آ رہی ہے۔ | `vomiting.wav` | P0 |
| 7 | `DIZZINESS` | `DIZZINESS` | مجھے چکر آ رہے ہیں۔ | `dizziness.wav` | P0 |
| 8 | `BREATHING_PROBLEM` | `BREATHING_PROBLEM` | مجھے سانس لینے میں مشکل ہو رہی ہے۔ | `breathing_problem.wav` | P0 |
| 9 | `BLEEDING` | `BLEEDING` | مجھے خون آ رہا ہے۔ | `bleeding.wav` | P0 |
| 10 | `NEED_HELP` | `HELP` | مجھے مدد چاہیے۔ | `need_help.wav` | P0 |
| 11 | `EYE_PAIN` | `EYE_PAIN` | میری آنکھ میں درد ہے۔ | `eye_pain.wav` | P1 |
| 12 | `BACK_PAIN` | `BACK_PAIN` | میری کمر میں درد ہے۔ | `back_pain.wav` | P1 |
| 13 | `WEAKNESS` | `WEAKNESS` | مجھے کمزوری محسوس ہو رہی ہے۔ | `weakness.wav` | P1 |
| 14 | `INJURY` | `INJURY` | مجھے چوٹ لگی ہے۔ | `injury.wav` | P1 |
| 15 | `ALLERGY` | `ALLERGY` | مجھے الرجی ہے۔ | `allergy.wav` | P1 |

All Urdu strings above are **drafts pending review by a fluent Urdu speaker** ([Content Guidelines](CONTENT_GUIDELINES.md)). Each also needs a `kokoro_input` Devanagari line authored and verified by ear.

### Answer messages

| Code | Concepts | Urdu | Audio file |
|---|---|---|---|
| `YES` | `YES` | جی ہاں۔ | `yes.wav` |
| `NO` | `NO` | جی نہیں۔ | `no.wav` |

## 4. Duration combinations — bounded on purpose

Composing duration into the message text produces a combinatorial problem: 15 symptoms × 4 durations = 60 messages, each needing its own reviewed Urdu string, `kokoro_input` and WAV. That is not a Day-4 task.

**Rule:** pre-generate duration combinations **only** for the demo-critical symptom. Everything else falls back to the base message.

| Code | Concepts | Urdu | Audio file |
|---|---|---|---|
| `CHEST_PAIN_TWO_DAYS` | `CHEST_PAIN + TWO + DAY` | مجھے دو دن سے سینے میں درد ہے۔ | `chest_pain_two_days.wav` |
| `FEVER_TWO_DAYS` | `FEVER + TWO + DAY` | مجھے دو دن سے بخار ہے۔ | `fever_two_days.wav` |

Both exist because the demo's symptom step swaps to `FEVER` under the pain-free fallback.

If a patient signs a symptom plus a duration with no matching template, the app shows the recognised concepts and speaks the **base** message — it does not invent a sentence and does not silently drop the duration from the display.

## 5. Demo script coverage check

From [Demo Plan](DEMO_PLAN.md), the exact live consultation and what each step requires:

| Step | Action | Requires Reliable | Requires audio |
|---:|---|---|---|
| 1 | Patient signs symptom | `CHEST_PAIN` (or `FEVER`) | `chest_pain.wav` / `fever.wav` |
| 2 | Doctor asks "Since when?" | — | phrase `DOCTOR_SINCE_WHEN` + PSL video |
| 3 | Patient signs duration | `TWO`, `DAY` + symptom sign | `*_two_days.wav` |
| 4 | Doctor asks breathing question | — | phrase `DOCTOR_BREATHING_DIFFICULTY` + PSL video |
| 5 | Patient answers | `YES` or `NO` | `yes.wav` / `no.wav` |

**Pre-freeze gate:** every row above must be green before the vocabulary is frozen. The `v_demo_readiness` view exists to answer this without a meeting.

## 6. Day-1 five signs — chosen from this list

[Day-1 Experiment](DAY1_EXPERIMENT.md) needs five visually distinct signs. They should also be signs the product actually uses, so Day-1 work advances Day-3 work:

| Day-1 sign | Visually distinct | Used by |
|---|---|---|
| `YES` | ✔ | demo answer |
| `NO` | ✔ | demo answer |
| `HELP` | ✔ | message 10 |
| `FEVER` | ✔ | message 4, demo step 1 fallback |
| `COUGH` | ✔ | message 5 |

`YES` and `NO` are included deliberately despite being the highest-risk confusion pair — if they cannot be separated, the team needs to know on Day 1, not Day 5. `DOCTOR` is excluded: visually distinct, but used by nothing.

## 7. Doctor phrase library — P0 ten and categories

Fifteen candidates, ten are P0. Categories make the doctor side faster to operate.

| Category | Code | Phrase | Urdu | P | Demo |
|---|---|---|---|:--:|:--:|
| Basic | `DOCTOR_UNDERSTAND` | Do you understand? | کیا آپ سمجھ گئے؟ | P0 | |
| Basic | `DOCTOR_WAIT_HERE` | Please wait here. | براہِ کرم یہاں انتظار کریں۔ | P0 | |
| Pain | `DOCTOR_WHERE_PAIN` | Where is the pain? | درد کہاں ہے؟ | P0 | |
| Pain | `DOCTOR_SINCE_WHEN` | Since when? | کب سے؟ | P0 | ✔ |
| Pain | `DOCTOR_PAIN_SEVERE` | Is the pain severe? | کیا درد شدید ہے؟ | P0 | |
| Symptoms | `DOCTOR_FEVER` | Do you have fever? | کیا آپ کو بخار ہے؟ | P0 | |
| Symptoms | `DOCTOR_COUGH` | Do you have a cough? | کیا آپ کو کھانسی ہے؟ | P0 | |
| Symptoms | `DOCTOR_VOMITING` | Are you vomiting? | کیا آپ کو قے آ رہی ہے؟ | P0 | |
| Symptoms | `DOCTOR_DIZZY` | Do you feel dizzy? | کیا آپ کو چکر آ رہے ہیں؟ | P0 | |
| Symptoms | `DOCTOR_BREATHING_DIFFICULTY` | Difficulty breathing? | کیا سانس لینے میں مشکل ہے؟ | P0 | ✔ |
| Medical | `DOCTOR_ALLERGY` | Allergic to any medicine? | کیا آپ کو کسی دوا سے الرجی ہے؟ | P1 | |
| Medical | `DOCTOR_TAKEN_MEDICINE` | Have you taken any medicine? | کیا آپ نے کوئی دوا لی ہے؟ | P1 | |
| Medical | `DOCTOR_INJURY` | Did you have an injury? | کیا آپ کو چوٹ لگی ہے؟ | P1 | |
| Medical | `DOCTOR_NEED_TEST` | We need to perform a test. | ہمیں ٹیسٹ کرنا ہوگا۔ | P1 | |
| Medical | `DOCTOR_TAKE_MEDICINE` | Take this medicine. | یہ دوا لیں۔ | P1 | |

Every enabled phrase needs a verified PSL video **and** demo-playback permission for that video — invariant I2. A phrase whose PSL cannot be verified is removed, not improvised (D013).

## 8. Coverage rules

| Rule | Enforcement |
|---|---|
| A message is demoable only if every one of its concepts is `Reliable + Enabled` | I1 |
| A message with pre-generated audio is playable only if the audio checksum matches its current text | I3 |
| A doctor phrase is demoable only if PSL-verified **and** demo-permission granted | I2 |
| Every demo-critical sign must be `Reliable` before vocabulary freeze | `v_demo_readiness`, checked Day 5 |
| Removing a weak sign automatically disables every message that used it | I1 cascade |
| The publicly quoted sign count is `v_production_vocabulary` only | [Judge Q&A](JUDGE_QA.md) |

The last two matter most. When a weak sign is removed on Day 5, the messages depending on it must disappear from the demo automatically — discovering the dependency by watching a demo step fail is the failure mode this whole document exists to prevent.

## 9. Content authoring checklist per message

- [ ] Concept sequence defined and all signs on the freeze list
- [ ] Urdu string drafted
- [ ] Urdu reviewed by a fluent Urdu speaker
- [ ] `kokoro_input` Devanagari authored
- [ ] Audio generated with the selected Kokoro voice
- [ ] Audio **verified by ear** by an Urdu speaker
- [ ] `audio_source_checksum` recorded
- [ ] Row enabled in the database
- [ ] Appears correctly in `v_demoable_messages`
