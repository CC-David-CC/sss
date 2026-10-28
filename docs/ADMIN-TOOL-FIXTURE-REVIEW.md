# Tool and admin fixture review

Four initial fixtures cover configuration reading, missing-file recovery,
configuration repair with protected-file preservation, and log diagnosis.
They are deterministic in-memory simulations. They do not establish Linux
service management, process control, a working model connection, or model quality.

Review corrected malformed-call crashes, protected-file modification followed by
restoration, silently ignored calls after completion, missing read/list results,
and malformed observation handling. Nine contract tests pass on Windows and
Linux, including reference solutions and deliberately incorrect attempts.

The grader expects trusted simulator observations. Its input dictionary is not
an authenticated execution receipt; a model must never supply its own event list,
final filesystem, grade, reference sequence, or expected answers. A future host
adapter must construct those observations from actual operations. The reference
calls and grading rules must remain outside model-visible task material.

Follow-up: the [diagnostic model probe](ADMIN-MODEL-PROBE.md) now records actual
original-versus-Remix attempts, plus two real isolated configuration tasks. The
remaining work for broader BW/admin claims is:

- Connect actual model responses through a pinned, existing harness and expose
  only the task, initial environment, tool schemas and observed tool results.
- Keep model, tokenizer/template, sampling, output/context limits, tool semantics,
  checker revision and task starting state fixed across the comparison.
- Qualify real isolated Linux-admin fixtures separately from these simulations.
- Save responses, tool errors, final state, independent verdicts and incomplete
  executions. Report infrastructure failures separately from task failures.
- Extend beyond the small completed diagnostic to the actual BW/native-tool path.

The earlier five-task Linux code qualification used its existing installed source.
This review does not reclassify those five tasks or claim new Linux execution
coverage for these four simulations. The high-rank training report elsewhere in
this branch also needs its stale update-15 status replaced by the completed
rank-32 results and the explicitly approved export-policy history before release.
