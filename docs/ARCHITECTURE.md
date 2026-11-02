# Final implemented architecture

This is the native GR00T N1.7 / LIBERO / Panda course project, not GR00T+WBC. Existing pretrained policy weights are frozen; no new policy training or custom EEF decoder is introduced.

Trusted TaskSpec independently defines the authorized object. Observation and actual policy instruction enter GR00T. The policy proposes16 native controls. The execution boundary assesses up to8 controls and either executes that exact prefix or executes no new controls and ends the episode. Re-observation follows acceptance; the episode cap is720 policy controls, after10 settling controls.

## B0 / A0 / G

B0: native baseline without task-authorization Gate. A0: current consecutive non-target bilateral-contact streak, checked at8-control chunk boundaries; it does not latch ended contacts or interrupt within a chunk. G: actual contact history plus isolated shadow prediction of up to8 controls; reject if a non-target streak reaches frozen k=3. Prediction does not write main physical state or policy RNG, and accepted raw actions are not rewritten.

The actual wrong-lift Oracle is independent: non-target lift at least2cm for2 controls with bilateral carry evidence and1cm relative-motion tolerance. Scoring a contact precursor is not directly observing every future wrong lift. Task labels, fault flags, Oracle outcomes and policy language are excluded from the contact-only scorer.

`tase/` implements task identity, scoring, shadow state and execution; `e3/` adds A0, native lifecycle, immutable ledger and4/6-cell checkpoints. `operator_engineering/` orchestrates exact-version admission and custody without replacing policy or scientific logic.

See frozen E2 and E3 reports and `SOURCE_PROVENANCE.json`. No future-action certificate, real-hardware, population zero-risk, universal reactive-baseline superiority, task recovery or hard20Hz guarantee is supported.
