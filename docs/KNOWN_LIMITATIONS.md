# Known Limitations

State these plainly. They are the price of a system that is honest about what it does.

## Vocabulary
Supports a limited healthcare vocabulary, not all PSL.

## Continuous language
Does not claim unrestricted continuous PSL translation. One completed motion produces at most one sign; signing continuously without pauses is not supported.

## Regional variation
Recognizes the verified signs and variants represented in project data. PSL regional differences exist, and a signer using another variant may not be recognized.

## Signer diversity
Hackathon testing covers a limited number of people. Augmented reference variants do **not** add signer diversity and are never counted as people.

## Urdu speech is Kokoro's Hindi voice
Kokoro does not officially support Urdu. We use its Hindi capability because spoken medical Urdu and everyday Hindi are phonologically close, and we feed it a hand-authored Devanagari pronunciation string.

**We do not claim Kokoro supports Urdu.** Pronunciation of specific medical terms may be imperfect, and each message is checked by ear rather than assumed correct.

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
