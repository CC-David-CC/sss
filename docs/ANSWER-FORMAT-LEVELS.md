# Score skill answers and answer formatting as separate skills

The current direct screen demands both a correct answer and the requested output
format. Its JSON condition reports `format_valid` and `answer_correct` separately,
but correct-answer scoring only occurs when valid JSON is present. That condition
therefore does not yet isolate the two capabilities.

Use three matched levels for each task family:

1. **Skill answer:** direct unstructured response; a task-specific independent
   semantic checker extracts and scores the answer. Record extraction confidence
   and ambiguity separately. Never turn an ambiguous parse into a pass.
2. **Format only:** provide the known correct answer and ask the model to encode it
   in the required schema. The checker measures syntax, required keys/types and
   exact value preservation. No underlying math or reasoning is needed.
3. **Skill plus format:** solve a fresh task and return the answer under the same
   schema. Score semantic answer correctness and format validity as two fields;
   report joint success only when both pass.

Train answer skill and format protocol as separate lesson groups. Then use a third
composed group with new values to measure whether the model can do both. A formatting
lesson may teach delimiters, JSON keys or value types, but must not contain the hidden
answer to an assessed skill task. A skill lesson may teach the operation without
teaching the format when that factor is being isolated. Mixed review measures whether
format lessons interfere with skill answers and vice versa.

For reasoning mode, add a parallel axis: final answer validity and each checkable
reasoning step. This yields skill answer, reasoning validity, format validity and
joint execution as separate observations. Long explanations are not rewarded unless
their steps can be checked; concise direct-answer behavior is its own condition.

Training metadata must bind each example's `lesson_kind` (`skill`, `format`, or
`composed`), `answer_mode` (`direct` or `reasoning`), supervised token spans, checker
identity and split. Native masks must prove which spans receive loss. A trainer must
not infer supervision from JSON shape or free-text tags. This metadata and the
currently added mode validator do not yet qualify real mixed-format native updates.

The first JSON screen was intended as condition 3, but a universal envelope broke
native proof-task schemas. Its aggregates are invalid for capability comparison;
see [the audit](FORMAT-SCREEN-AUDIT.md). It is not the three-level ablation or
mastery qualification.
