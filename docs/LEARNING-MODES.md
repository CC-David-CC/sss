# Primitive purpose and answer modes

An independent primitive task measures one stated skill. Composition is a separate
gate. Formatting requirements are scored separately from semantic task correctness
where an independent, unambiguous extraction/check is available; ambiguous output
is not silently repaired into a pass.

Answer mode is explicit: direct answer or reasoning. Reasoning-mode practice can
supervise answer tokens only, or both verified reasoning and answer tokens.
The latter requires a verified demonstration and explicit native loss-mask binding.
The new `learning_modes.validate_mode` validates metadata only. It does not install
a curriculum, construct masks, or qualify reasoning-mode inference/training.

Track final-answer correctness, format compliance, natural completion, and reasoning
validity independently. Reasoning validity requires a checkable trace, such as proof
steps or arithmetic transitions; fluent prose and correct final answers alone do not
establish a valid trace. Different mode prompts, token limits, templates, target spans
and native masks must be recorded; compare models within the same condition.

Legacy duplicate families are superseded for this diagnostic by
`sss.primitive_rewrite`: Boolean truth tables, four canonical deduction evidence
statuses, and signed decimal rounding including ties. Finite Boolean cases are not
inflated by renamed variables. Rounding uses decimal inputs to avoid additionally
testing fraction conversion. Old generator definitions and results remain preserved.

The completed preliminary direct-answer independent screen used 408 checked distinct
questions across 51 other foundational skills, plus 26 rewritten cases across six
families. Original FP32 scored 47/408 and 9/26; Remix 2 FP32 scored 165/408 and 22/26.
Combined: 56/434 versus 187/434. These are custom development diagnostics, not mastery
qualification, reasoning-mode scores, or comparisons to the earlier 864-question set.
The intermediate finite-dedup diagnostic is superseded by the rewritten six-family
panel; do not add its results to these totals or present it as a repeated-seed study.

No new training occurred. Existing lesson service, training runner, working-parent
decision and protected assessments remain responsible for candidate execution and
acceptance. Reasoning/direct conditions must be bound there before training either.
