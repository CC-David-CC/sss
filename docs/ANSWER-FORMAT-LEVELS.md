# Answering and formatting are separate skills

The curriculum must teach and measure three levels. A model can know the answer
but express it in the wrong shape; it can also produce perfect JSON containing a
wrong answer. Those are different failures and must not share one score.

| Level | What the model must do | What the checker scores | Training target |
|---|---|---|---|
| 1. Answering | Solve the skill task and give its answer without an added format demand | Semantic correctness under the task's own checker | The skill answer; no special output-schema lesson |
| 2. Formatting | Receive the correct content and encode it in a requested format | Syntax/schema validity and preservation of the supplied content, as separate fields | Formatting behavior using known answers; no hidden skill task to solve |
| 3. Answer + format | Solve a fresh skill task and encode the answer in the requested format | Answer correctness, format validity, and joint success, all reported separately | A composed lesson only after the first two levels; use fresh values and examples |

## Measurement rules

1. **Keep checkers independent.** The answer grader applies the skill's semantic
   rules. The format grader applies that task's declared response schema. Do not
   make semantic correctness conditional on passing a JSON parser. When a malformed
   response still contains a recoverable answer, score the answer with a
   task-specific tolerant extractor and record format failure separately. If the
   answer cannot be recovered, mark that answer score unscorable; do not silently
   turn a formatting failure into a knowledge failure.
2. **Use native task contracts.** A proof task may require a proof object; a numeric
   task may require a number or a specific numeric object. Do not wrap every task in
   a universal `{"answer": ...}` envelope. Check both schema validity and, where
   relevant, whether formatting preserved the known or computed answer.
3. **Keep the three levels' data separate.** Format-only examples disclose the
   correct content by design and must not be counted as skill practice. Composition
   evaluation uses new skill inputs, not the examples used to teach the format.
   Hold out cases across all three levels.
4. **Report denominators and failures by level.** At level 3, report answer accuracy,
   format-valid rate, answer-preservation rate, and joint pass rate. A single
   all-or-nothing percentage hides which capability needs practice.

## Reasoning is a crossed mode, not a substitute for these levels

Direct-answer and reasoning behaviors are a separate axis. Measure them alongside
the levels above rather than merging them into “formatting” or “answering.” A
reasoning condition needs its own checkable reasoning target and final-answer score;
verbosity alone is not evidence of valid reasoning. The curriculum can therefore
compare direct and reasoning examples at the answering level, format-only level,
and composed level when suitable checkers exist.

## Training and current implementation status

Author and train separate lesson groups for answering and formatting, then introduce
composition as its own group. Preserve mixed review across earlier levels to detect
interference. Bind every example to its level, answer mode, checker, data split, and
supervised token spans. PCC's native loss masks must confirm which spans actually
receive loss; metadata labels alone do not establish that the intended training
occurred.

S³ currently has direct skill checkers and answer/reasoning-mode metadata, but the
recent foundation screens combined semantic answering with strict output expectations.
They cannot isolate a formatting weakness from a skill weakness. The first generic
JSON screen is invalid for broad comparison because it replaced task-native proof
schemas; see [the audit](FORMAT-SCREEN-AUDIT.md). Its aggregate scores are excluded.

`sss/learning_levels.py` validates lesson/evaluation conditions and keeps answer,
format-only, composed, and reasoning verdicts separate. The frozen integration is
`sss/level_evaluation.py`: it makes matched answer/direct and answer/reasoning cases,
a format-only case, and composed direct/reasoning cases. It calls the existing model
callback shape and records separate answer, reasoning, format, preservation, and joint
rates. A reasoning result is scored only when the harness supplies a normalized
separate reasoning field; otherwise the condition is reported unavailable, not wrong.
Direct mode remains the default. Callers can request both modes with
`answer_modes=('direct', 'reasoning')`; this currently succeeds only for exact
integer-addition cases, where an independent checker exists. The panel supports only
declared exact-scalar skill families.
Its `math.exact-scalar.answer-object.v1` schema is never applied to proof, array,
tool, or other task types. Cases are frozen and bound to profile, catalog, generator,
and checker source hashes; evaluation is diagnostic and cannot qualify or promote.

`sss/learning_lessons.py` creates verified synthetic practice lessons for those same
three levels. It accepts practice cases only, checks the reference with the task
checker, keeps reasoning, answer, and format output spans separately labeled, and
requires a model-specific renderer. The initial independently checked reasoning
adapter is deliberately limited to exact integer addition: it verifies the operands
and arithmetic in one equation. It does not treat arbitrary prose from a model as
verified reasoning. Format-only lessons remain direct and disclose the correct answer.
`build_scalar_pcc_lesson` writes an immutable S³ episode
archive and emits PCC schema 2 with checker, renderer, tokenizer and archive hashes.
`admit_scalar_pcc_lesson` submits once, rereads the saved lesson, and compares PCC's
persisted tokens, targets and mask with S³'s expected tokenization before returning
an admission receipt. The native PCC policy names distinguish `answer_only`,
`reasoning_and_answer`, `format_only`, `answer_and_format`, and
`reasoning_answer_and_format`. PCC consumes the resulting mask at its token-level
cross-entropy loop.

Validation on 2026-10-28: the S³ suite passed on Windows (155 passed, 12 skipped)
and on llm-79 Linux CPU (155 passed). PCC lesson/segment tests passed (23); BW
learning and lesson tests passed (22); the S³-to-PCC admission test passed. The
native CPU integration then sent five S³ lessons through BW and PCC: direct answer,
checked-reasoning answer, format-only, direct composed, and checked-reasoning
composed. PCC's saved token IDs, targets, and loss mask matched S³'s expected values;
the native request contained the same mask; and one full-weight CPU update completed
for each policy. The base fixture stayed unchanged and no candidate was promoted.
The generated tiny GGUF is a wiring fixture, not a language model. Lower training
loss on this fixture proves the update path executed; it does not establish that a
model learned arithmetic or improved. The machine-readable evidence is in
[`validation/response-level-native-cpu-20261028/result.json`](../validation/response-level-native-cpu-20261028/result.json).
Build pins, source hashes and binary identity are recorded in the accompanying
[`provenance.json`](../validation/response-level-native-cpu-20261028/provenance.json).

The numeric panel is currently programmatic and limited to exact scalar families.
Its score contract does not replace the existing qualification policy. A larger
model-specific campaign must pin profile, prompt/renderer, and checkers, then keep
answer-only, known-answer format-only, and fresh composed outcomes in distinct
reports. Extend the same adapter pattern to native proof, array, and tool schemas
before claiming coverage outside exact scalar tasks.
