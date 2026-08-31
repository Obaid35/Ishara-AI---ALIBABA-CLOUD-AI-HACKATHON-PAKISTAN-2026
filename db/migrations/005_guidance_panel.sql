-- Guidance panel: a help drawer on the patient screen showing each supported
-- sign's reference video, so a signer who does not remember the exact movement
-- can copy it instead of guessing. Guessing produces an unknown at best and a
-- wrong sentence at worst.
--
-- Off by default. It shows a camera-facing panel during a real consultation, so
-- turning it on is a deliberate choice by an admin, not something a fresh
-- install does on its own.

INSERT INTO settings (key, value)
VALUES ('guidance_panel_enabled', 'false'::jsonb)
ON CONFLICT (key) DO NOTHING;
