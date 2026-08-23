# Judge Q&A

## Product and scope

### Does this translate all PSL?
No. It supports a limited, verified healthcare vocabulary. We chose reliability over an exaggerated vocabulary claim.

### Why only 15–30 signs?
Because a smaller set tested on new signers is more meaningful than a large set that only works on source data.

### Can it replace an interpreter?
No. Complex or sensitive consultations may still require a qualified interpreter.

### Does it diagnose?
No. Communication assistance only.

### Can the doctor reply?
Yes, through a small fixed library of verified PSL medical responses, grouped by category.

## Data and method

### Did you use existing PSL videos?
Yes, as a bootstrap experiment and reference. We measured transfer to live people and add recordings only where evidence shows they are needed.

### Why not simply train from one video per sign?
One or few examples are not a diverse training dataset. We use DTW reference matching and augmented variants, then validate on new signers. Augmented variants are never counted as additional people.

### Why DTW and not a neural network?
Because we started with a handful of reference clips. Committing to a temporal classifier before knowing our data situation would have been guessing. If the evidence justifies one, the architecture allows it — but that decision follows the data.

### What is the accuracy?
Report the actual final test result with its denominator, number of people, the unseen-person result specifically, and the reliable sign count. **Never quote an unmeasured number, and never a percentage without its denominator.**

### Why is the unknown rate so high?
Deliberate. We tune the gate so wrong answers stay under 2%, accepting roughly one retry in five. For medical communication, "please repeat" is a much cheaper error than a confidently wrong sentence spoken to a doctor.

## Safety

### How do you prevent dangerous wrong speech?
Three layers. The unknown gate can refuse to classify — it requires both an absolute match quality and clear separation from the runner-up. The patient sees the result before anything is spoken. And nothing is ever spoken without an explicit patient action.

### What if the doctor's spoken question is misheard?
The matched phrase is shown for confirmation before the PSL video plays. Speech only selects from our verified list — the system never generates PSL.

### What about PSL regional differences?
The prototype supports the verified variants represented in our data. Regional variation is a known limitation and a future expansion area.

## Technology

### What is the stack?
Next.js and React on the front end, FastAPI and Python on the back end, PostgreSQL for content. MediaPipe Holistic for tracking, DTW for recognition, Kokoro for Urdu speech, and verified PSL videos for the doctor direction.

### Is the Urdu voice a real Urdu model?
No, and we are explicit about it. Kokoro does not officially support Urdu, so we use its Hindi voices with a hand-authored pronunciation string, because spoken medical Urdu and everyday Hindi are phonologically close. Each sentence is checked by ear by an Urdu speaker.

### Does it need internet?
No. The entire demo runs with the network adapter disabled. Only the optional doctor voice input uses a cloud model, and it falls back to a local model and then to the buttons.

### Do you use an LLM?
Not for the medical output. Recognized concepts map to pre-written, reviewed Urdu sentences through a lookup table, so the system cannot hallucinate a medical statement.

### Why web?
A browser-based one-screen interface can run on an ordinary clinic laptop with minimal workflow change.

## Product decisions

### Why doesn't the patient log in?
Because a Deaf patient arriving in pain should not face account, email, password and OTP before they can say what hurts. It is an accessibility and emergency-use decision.

### Then why is there a login at all?
For staff. It provides settings, content management and an audit trail over verified medical content. It never sits in front of the camera.

### Do you store the conversation?
No. Session history is visible during the consultation and cleared when it ends. There is no transcript table and no patient record.

### How do you stop unverified content reaching a patient?
The database refuses it. A message cannot be enabled unless every sign it uses is reliable; a doctor phrase cannot be enabled without PSL verification and playback permission; audio that no longer matches its on-screen text cannot play. These are constraints, not conventions.

## If something fails during the demo

Say plainly what happened and which fallback is running. The system is built so that no single failure stops the consultation: database → snapshot, cloud speech → local → buttons, live demo → backup recording. Showing that the fallbacks work is a better answer than pretending nothing broke.
