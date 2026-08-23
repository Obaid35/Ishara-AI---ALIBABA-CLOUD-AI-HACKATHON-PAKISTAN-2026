# UI Specification

Governs the communication screen (`/`). Admin pages follow the same [Design System](DESIGN_SYSTEM.md) but are conventional data screens — see [Admin Specification](ADMIN_SPEC.md).

## Screen model

One application screen. No required scrolling on the demo laptop.

```text
┌──────────────────────────────────────────────────────────────────┐
│ Ishara AI   Patient → Doctor | Doctor → Patient   + New   Dr. A │
├───────────────────────────────┬──────────────────────────────────┤
│                               │ Status                           │
│       LIVE CAMERA             │ Recognized: CHEST PAIN           │
│                               │ Urdu: سینے میں درد               │
│   optional tracking overlay   │                                  │
│                               │ Current Message                  │
│                               │ مجھے سینے میں درد ہے۔            │
│                               │                                  │
│                               │ [ Speak ] [ Undo ] [ Clear ]     │
├───────────────────────────────┴──────────────────────────────────┤
│ Communication assistance prototype — not diagnostic.             │
└──────────────────────────────────────────────────────────────────┘
```

## Header

- Ishara AI brand.
- Two-mode switch.
- `+ New Conversation`.
- Signed-in staff name and logout **when staff are signed in**.
- Optional small camera/system status.
- Degraded-mode indicator when running on snapshot, live TTS or local STT.

When nobody is signed in, the header shows brand, mode switch and New Conversation only. **The patient experience does not change with login state.**

Avoid large menus, profiles, sidebars. Admin navigation does not appear on this screen — it lives at `/admin`.

## Patient mode — left

- large live camera;
- face, upper body, both hands visible;
- optional subtle tracking overlay;
- camera guidance if needed.

## Patient mode — right

### Status
Ready / Reading / Recognized / Please Repeat / Not Recognized.

The two unknown states are worded and coloured differently — amber for ambiguous, red for no match. Collapsing them discards information the patient can act on.

### Current message
The visual hero. Largest text on the screen. Remains visible until the user changes or clears it.

### Session history
A compact, scrollable list of what has been said in this consultation, patient and doctor turns distinguished. Cleared by `+ New Conversation` and at session end.

### Controls
- Speak (primary)
- Undo
- Clear
- Retry when needed

## Doctor mode

Left: selected PSL video with play / pause / replay / full-screen.
Right: phrase library grouped by category (Basic, Pain, Symptoms, Medical) with a search field, and the selected phrase.

Optional microphone button when doctor voice input is enabled. When a phrase is matched from speech, it appears as a **confirmation prompt** — not as immediate playback.

## Accessibility

- strong contrast;
- large Urdu;
- **status never by color alone** — always icon or text as well;
- large click/touch targets;
- critical text stays visible;
- no auto-speech;
- **no account required to use the communication screen.**

The last point is an accessibility requirement, not a convenience. A Deaf patient in pain must not have to authenticate.

## Responsive behavior

Laptop/desktop: no page scroll on `/`.
Tablet: two columns if possible.
Mobile: scrolling acceptable; mobile is not P0.

Admin pages scroll and paginate normally at every size.
