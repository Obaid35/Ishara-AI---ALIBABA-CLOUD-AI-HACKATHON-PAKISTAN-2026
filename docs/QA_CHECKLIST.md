# Final QA Checklist

## Environment
- [ ] PostgreSQL running, migrations applied.
- [ ] JSON snapshot exported **after** the last content change.
- [ ] App verified to boot with PostgreSQL stopped (snapshot mode).
- [ ] `.env` present locally, gitignored, no credential in any committed file.
- [ ] `assets/audio/` populated; `assets/psl-videos/` complete for every enabled phrase.
- [ ] **Full demo run with the network adapter disabled.**

## Camera
- [ ] Opens without refresh.
- [ ] Face, upper body and hands fit.
- [ ] Permission denial handled.
- [ ] Normal room lighting tested.
- [ ] Sitting/standing behavior checked.

## Recognition
- [ ] Reliable sign count frozen.
- [ ] Thresholds frozen; freeze recorded in the audit log.
- [ ] Unknown signs are not forced.
- [ ] Ambiguous and no-match states both reachable and correct.
- [ ] One motion produces at most one decision.
- [ ] Every demo sign tested on another person.
- [ ] YES/NO separately verified.
- [ ] Weak signs removed or improved — and dependent messages auto-disabled.
- [ ] Reference `extractor_version` matches the installed MediaPipe version.

## Message
- [ ] Urdu wording correct and reviewed by a fluent speaker.
- [ ] No diagnosis added.
- [ ] No severity/duration invented.
- [ ] Unsupported sequences show concepts, not an invented sentence.
- [ ] Undo works.
- [ ] Clear works.
- [ ] Retry works.
- [ ] Speak requires explicit action.
- [ ] `+ New Conversation` clears concepts, sentence, history and selected phrase.

## Audio
- [ ] Every P0 message has pre-generated audio.
- [ ] **No message shows a stale-audio warning** — checksums current.
- [ ] Audio verified by ear by an Urdu speaker.
- [ ] Volume sufficient on the demo laptop.
- [ ] No internet required for any audio in the demo.

## Doctor mode
- [ ] Every displayed PSL video verified.
- [ ] Rights/permission granted for demo playback on every enabled phrase.
- [ ] Categories and search work.
- [ ] Play/replay/full-screen work.
- [ ] Return to Patient mode works.
- [ ] If voice input is on: matched phrase confirmed before playback; failure falls back to buttons silently.

## Application shell (if built)
- [ ] Patient can use `/` with no login.
- [ ] Staff login works; logout revokes the session immediately.
- [ ] Deactivating a user blocks access immediately.
- [ ] Admin routes reject non-admin roles **server-side**, not only in the UI.
- [ ] No public signup route exists.
- [ ] Session history clears at session end and is never written to the database.

## UI
- [ ] No page scroll on the communication screen on the demo laptop.
- [ ] Urdu message is the visual hero.
- [ ] `#017A3A` theme consistent.
- [ ] Status uses icon/text, not only color.
- [ ] Degraded-mode indicator visible when on snapshot, live TTS or local STT.
- [ ] No unnecessary navigation on `/`.

## Demo
- [ ] Exact flow rehearsed 10 times.
- [ ] At least 9/10 successful without developer intervention.
- [ ] `v_demo_readiness` shows nothing outstanding.
- [ ] `v_permission_gaps` is empty.
- [ ] Backup recording exists locally plus a second copy.
- [ ] Laptop charged and charger packed.
- [ ] Browser notifications disabled; no pending restart or update.
