# Audit: JSON answer envelope screen

The preliminary structured-format screen used one outer `{"answer": value}` schema
for all 408 tasks and both models. This is invalid as a broad skill comparison.

Evidence: the task families `logic.joint_premises` and `logic.proof` request their
own structured proof objects. Both models returned those task-shaped JSON values,
not the added outer envelope. The harness marked them format-invalid and did not
score the underlying proof task. A required schema mismatch overwhelmed the
intended answer-mode measurement. Preserve raw requests, outputs and aggregate
results for tooling diagnosis, but do not compare its aggregate `answer_correct`
totals to the direct screen or call them model skill scores.

Future assessment needs per-task response schemas bound to task definitions. Report
syntax/schema validity separately from semantic correctness. For proof tasks,
validate the required proof object and the proof itself. For numeric tasks, accept a
well-defined numeric representation and grade its value. If a universal envelope is
itself under study, test that as a separate formatting lesson using known answers;
then test skill plus envelope on fresh cases. Never replace a task's required schema
with a universal wrapper without qualifying the task contract.

No training examples or weights were changed by this screen. This is a harness/test
design failure and an explicit recovery record, not a model failure.
