-- Keep the shape of what was actually captured for each live attempt.
--
-- A wrong answer with a very low distance means the captured window did not
-- contain what we think it did. Without the duration and the sequence itself
-- there is no way to tell a mis-segmented capture from a genuinely ambiguous
-- sign, and the two need opposite fixes.

ALTER TABLE recognition_trials
    ADD COLUMN IF NOT EXISTS capture_frames  integer,
    ADD COLUMN IF NOT EXISTS capture_ms      integer,
    ADD COLUMN IF NOT EXISTS hand_visibility numeric,
    ADD COLUMN IF NOT EXISTS capture_path    text;
