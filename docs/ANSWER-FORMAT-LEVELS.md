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

`sss/learning_levels.py` now provides a strict condition validator and separate
answer, format-only, composed, and reasoning score functions. Its targeted unit tests
cover independent verdicts and unscorable checker errors. This is a pure scoring
contract: the S³ model evaluator does not yet generate or run all three matched
conditions, PCC has not confirmed per-example loss masks for these targets, and no
model training or improvement is claimed from this split.
