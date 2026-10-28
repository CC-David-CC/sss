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
format-only, composed, and reasoning verdicts separate. The first frozen integration
is `sss/level_evaluation.py`: it makes matched triplets, calls the same model callback
shape as the existing evaluator, and records per-level answer, format, preservation
and joint rates. It currently supports only declared exact-scalar skill families.
Its `math.exact-scalar.answer-object.v1` schema is never applied to proof, array,
tool, or other task types. Cases are frozen and bound to profile, catalog, generator,
and checker source hashes; evaluation is diagnostic and cannot qualify or promote.

`sss/learning_lessons.py` creates verified synthetic practice lessons for those same
three levels. It accepts practice cases only, checks the reference with the task
checker, keeps answer and format output spans separately labeled, and requires a
model-specific renderer. `build_scalar_pcc_lesson` writes an immutable S³ episode
archive and emits PCC schema 2 with checker, renderer, tokenizer and archive hashes.
`admit_scalar_pcc_lesson` submits once, rereads the saved lesson, and compares PCC's
persisted tokens, targets and mask with S³'s expected tokenization before returning
an admission receipt. The native PCC policy names distinguish `answer_only`,
`reasoning_and_answer`, `format_only`, `answer_and_format`, and
`reasoning_answer_and_format`. PCC consumes the resulting mask at its token-level
cross-entropy loop.

The S³ full unit suite passes on Windows and on llm-79's Linux CPU (153 tests on
llm-79). The PCC lesson and segment suites pass in WSL (23 tests); the response-level
mask cases also passed on llm-79. A cross-project integration test passed on both
Linux environments, creating each lesson through S³, admitting it to PCC, then
reading back and comparing the exact tokens, targets and loss mask. These checks
prove lesson admission and mask persistence, not that a native optimizer update
trained the intended spans. No model training run has used these new lesson types,
and no model improvement is claimed. Reasoning lesson generation still needs
independently checkable reasoning spans; the reasoning mask policy exists, but the
direct scalar lesson builder does not manufacture reasoning traces.

The numeric panel is currently programmatic and limited to exact scalar families.
Its score contract does not replace the existing qualification policy. A larger
model-specific campaign must pin profile, prompt/renderer, and checkers, then keep
answer-only, known-answer format-only, and fresh composed outcomes in distinct
reports. Extend the same adapter pattern to native proof, array, and tool schemas
before claiming coverage outside exact scalar tasks.
