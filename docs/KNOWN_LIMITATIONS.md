# Known Limitations

State these plainly. They are the price of a system that is honest about what it does.

## Vocabulary
Supports a limited healthcare vocabulary, not all PSL.

## Continuous language
Does not claim unrestricted continuous PSL translation. One completed motion produces at most one sign; signing continuously without pauses is not supported.

Concretely: a capture ends only after about 320 ms of stillness. A signer who runs one sign into the next never produces that gap, so the capture runs on until it aborts. **Every result we report comes from deliberate signing** — a fluent signer moves faster than our references and does not pause, and we have not tested that case because no fluent signer was available to the project. Sliding-window spotting is the known fix and is Phase 2 in the roadmap, gated on having fluent signers to validate against.

## Regional variation
Recognizes the verified signs and variants represented in project data. PSL regional differences exist, and a signer using another variant may not be recognized.

## Signer diversity
Hackathon testing covers a limited number of people. Augmented reference variants do **not** add signer diversity and are never counted as people.

## Urdu speech is Kokoro's Hindi voice
Kokoro does not officially support Urdu. We use its Hindi capability because spoken medical Urdu and everyday Hindi are phonologically close, and we feed it a hand-authored Devanagari pronunciation string.

**We do not claim Kokoro supports Urdu.** Pronunciation of specific medical terms may be imperfect, and each message is checked by ear rather than assumed correct.

## One sign carries one fixed sentence

A recognised sign is a **concept**, not a sentence. `HELP` means "help" — it
carries no subject, no tense and no intent. The Urdu it produces,
`مجھے مدد چاہیے۔` ("I need help"), adds all three.

The same sign could legitimately belong to many different utterances:

> "last night **my friend** needed help, that is how **I** got hurt — I slipped
> and fell on my foot"

Here `HELP` is about someone else, in the past, and the actual complaint is the
injury. The product cannot express that, and it never will with this design.

**This is a phrasebook, not a translator.** Each supported sign is bound to one
pre-written, reviewed sentence. What protects the patient is not the mapping
being right in general, but three things in the flow:

- the recognised concept (`HELP`) is displayed separately from the composed
  sentence, so it is visible what was recognised versus what was written for it;
- nothing is spoken until the patient reads the Urdu and presses Speak;
- Undo and Clear are always available if the sentence is not what they meant.

So the patient is never made to say something they did not approve — but they
are limited to the one phrasing per sign that we wrote. A patient whose meaning
falls outside that set cannot express it here, and needs an interpreter.

Wording that reflects this: the product **communicates a verified set of
utterances**. It does not translate what the patient is saying.

## Fixed sentences
Urdu output comes from pre-written reviewed templates, not generation. An unsupported combination of concepts shows the recognized concepts rather than a fluent sentence. This is a deliberate trade of flexibility for determinism.

## Medical usage
Communication aid only; not diagnosis or treatment.

## Doctor direction
Fixed verified phrase library, not unrestricted Urdu → PSL. Optional voice input only *selects* an existing verified phrase.

## Doctor voice input
Optional, requires internet for the primary path, and Urdu speech recognition is imperfect. It is a convenience over the buttons, never a dependency — and a misheard question is confirmed before anything plays.

## Complex consultations
Sensitive, legal, consent-heavy, or complex medical discussions may still require a qualified interpreter.

## Content rights
Third-party PSL videos may only be redistributed or embedded according to permission or licensing.

## Environment
Camera framing, occlusion, lighting and signing variation can affect recognition. Results apply to the signers and conditions actually tested.

## Unknown behavior
Retry/unknown is intentional and preferable to a confident wrong medical translation. The system is tuned to refuse rather than guess — expect roughly one retry in five, by design.

## No history
Consultations are not stored. There is no record to review afterwards, by design.

## Not a hospital system
No patient records, appointments, billing, or administration beyond managing the verified content itself.
