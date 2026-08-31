-- An aborted capture is not the same thing as "no reference matched".
-- The live harness records every attempt as it happens, so the stored outcome
-- must be able to say which of the two actually occurred rather than
-- flattening an abort into a no-match.

ALTER TYPE trial_outcome ADD VALUE IF NOT EXISTS 'aborted';
