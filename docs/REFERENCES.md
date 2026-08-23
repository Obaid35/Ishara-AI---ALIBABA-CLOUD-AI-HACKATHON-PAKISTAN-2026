# References

Use official or primary sources wherever possible.

## PSL resources

- Pakistan Sign Language: `https://psl.org.pk/`
- PSL About: `https://psl.org.pk/about`
- Deaf Reach / FESF: `https://deafreach.com/`

## Technology sources

Record the version actually installed alongside each — see the pinning table in [Technology Stack](TECH_STACK.md).

- MediaPipe (Holistic / Tasks): `https://ai.google.dev/edge/mediapipe`
- Kokoro-82M model card and voice list: `https://huggingface.co/hexgrad/Kokoro-82M`
- Groq speech-to-text models: `https://console.groq.com/docs/speech-to-text`
- Groq structured outputs (P2 only): `https://console.groq.com/docs/structured-outputs`
- faster-whisper: `https://github.com/SYSTRAN/faster-whisper`
- FastAPI · Next.js · PostgreSQL — official documentation

## Evidence to preserve in project records

- official PSL resource claims and current sign count;
- dictionary vs tutorial examples;
- FESF/content-owner permission response;
- vocabulary verification notes, with reviewer and date;
- volunteer consent, per purpose;
- Day-1 100-trial results, with per-trial distances;
- threshold calibration data and the freeze record;
- unseen-person results;
- Kokoro voice blind-test result;
- measured frame latency;
- installed versions of every pinned component.

## Presentation wording rule

Do not say:

- "PSL has zero technology support."
- "No PSL dataset exists."
- "This works for all Pakistani Deaf users."
- "Kokoro supports Urdu."
- "Our accuracy is X%" without a denominator and population.

Prefer:

- existing PSL digital resources exist, while practical real-time communication support remains limited;
- the prototype targets a small verified vocabulary;
- regional variation exists;
- results apply to the signers and conditions actually tested;
- Urdu speech uses Kokoro's Hindi voices, because spoken Urdu and Hindi are phonologically close;
- unknown and wrong are reported as separate numbers.
