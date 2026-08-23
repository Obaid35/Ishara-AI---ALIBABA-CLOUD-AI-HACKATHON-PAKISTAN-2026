# Design System

Applies to the whole application. The communication screen (`/`) is governed additionally by [UI Specification](UI_SPEC.md); admin pages are conventional data screens — see [Admin Specification](ADMIN_SPEC.md).

## Principles
1. Communication first.
2. One-screen clarity.
3. Large readable Urdu.
4. Patient control before speech.
5. Trust over spectacle.
6. Medical, not futuristic.
7. Minimal cognitive load.

## Typography
Use a clean sans-serif with strong Urdu support. Avoid decorative Urdu fonts.

Suggested scale:
- Urdu final sentence: 30–40px
- recognized Urdu concept: 24–30px
- main button: 16–18px
- section heading: 18–22px
- secondary/status text: 14–16px

## Spacing
Use an 8px rhythm: 8 / 12 / 16 / 24 / 32.

## Cards
- white surface;
- subtle border;
- 12–16px radius;
- minimal shadow;
- selected state may use green outline.

## Buttons
### Primary
Speak / selected PSL playback. Green background, white text, large height.

### Secondary
Undo / Replay. White background, border, dark text.

### Destructive
Clear. Never stronger visually than Speak.

## Mode switch
Two segments: Patient → Doctor / Doctor → Patient. Active green, inactive white.

## Status patterns
- Ready: neutral
- Reading: blue/info
- Recognized: green check + label
- Repeat: amber + instruction
- Unknown: red + retry instruction

## Camera
Rounded rectangle, full upper body and hands visible, optional subtle landmarks. Never cover the signer with heavy graphics.

## Urdu message card
The hero component. High contrast, largest text, remains visible until user changes/clears it.

## Animation
Only subtle state transitions. Avoid bouncing, glowing, constant pulsing, and cinematic effects.

## Admin pages

Same tokens — colour, type scale, spacing rhythm, card and button styles — applied to conventional data screens. Tables, filters, pagination and scrolling are all normal here; the no-scroll rule applies only to `/`.

Admin-specific patterns:

- **Status pills** for verification and reliability, using the status colours below, always with text as well as colour.
- **Blocked actions explain themselves.** A disabled Enable button states the reason — "STOMACH_PAIN is not Reliable" — never just "invalid".
- **Destructive-adjacent actions preview their effect.** Disabling a sign lists the messages that will be disabled with it, before confirming.
- **Warnings are inline, not toast-only.** Stale audio and permission gaps must remain visible on the row, because a dismissed toast is a missed problem.

## Degraded-mode indicator

A small persistent header chip when the app is running on the JSON snapshot, live TTS instead of pre-generated audio, or local STT. Neutral styling, never alarming — but never hidden. Silent degradation during a judged demo is worse than a visible one.
