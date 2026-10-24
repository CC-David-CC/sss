# Comparing harnesses by observed behavior

The smallest comparison has **four task executions for each task and harness**:

| Execution | Configuration | Evidence available to its editor |
| --- | --- | --- |
| Baseline | The pinned original harness | None from this task |
| General probe | A proposed improvement to general working habits | Baseline behavior |
| Task probe | A proposed improvement specific to this kind of task | Baseline behavior |
| Composed | A new configuration combining evidence-supported ideas | Baseline and both probes |

Propose and compose are additional model sessions. They do not replace the
executions that test their suggestions. A task execution may contain many model
and tool calls. Four harnesses (BW, OpenCode, Codex and pi) therefore require at
least **16 task executions per development task**, plus editing, checking and
follow-up evaluation. This is one fixed-sampling cycle, not four seed repeats.

This design is strengthened by ideas incorporated from
[Harness²: Recursive Agent Harnessing for an Open World](https://arxiv.org/abs/2610.14224),
from Northwestern and Google Cloud AI Research, submitted October 9, 2026.
The reviewed [experiment guide](https://github.com/google-research/harness2/blob/1cfe254e8d25b15f37048c3730134686abe60335/docs/EXPERIMENTS.md)
and source are pinned to `1cfe254e8d25b15f37048c3730134686abe60335`.
This module is an original implementation; no upstream code or examples were
copied. The existing [LearnHarness reasoning work](LEARNHARNESS-REVIEW.md)
addresses a different part of the curriculum and remains separately credited.

## What works now

`sss study harness` provides an offline specification, execution matrix,
behavior-only editor view and comparison report. It binds observations to the
original host operation, configuration, task, artifact and independent checker.
It separates incomplete or uncertain operations, infrastructure errors, wrong
answers and budget overruns. Missing evidence cannot become a pass.

The tests use **synthetic contract fixtures**, including deliberately corrupt
receipts, changed models, omitted probes, a gain with a regression, an unseen
task failure, missing retention controls and changed checker identities. These
tests establish the comparison machinery; they do not establish that any
harness or Wen improved.

Live exporters and proposer/composer integrations for all four harnesses are
still to be qualified. No four-harness performance result has been measured by
this increment. A hash in a JSON document is a binding, not proof that a host
ran honestly or that its isolation worked. A trusted host exporter must verify
the actual files, process receipts, model identity, effective settings and
runtime containment before producing this evidence. S³ checks that evidence;
it does not manufacture or replace it.

## Responsibilities

| Part | Responsibility |
| --- | --- |
| S³ | Skill/task definitions, comparison specification, evidence views, independent scoring, transfer and retention reports |
| BW / OpenCode / Codex / pi | Their actual execution loops, original operations, tool permissions, task settlement and exports |
| PCC | Fixed model inference, context identities, native receipts and separately measured weight updates |
| Operator | Qualified environments, access boundaries, exact source pins, resource limits and publication decisions |

The auditor is not a second BW workflow engine. It cannot run a shell, call a
model, acquire a GPU, change permissions, retry an operation or adopt a recipe.
BW's existing two-approach exploration can supply probe executions only after
an exporter checks the matching conditions and separate operation receipts.
Its selection result alone is not the composed fourth execution.

OpenCode, Codex and pi are host harnesses. DeepSeek and Qwen model families or
tool formats are another experimental axis; they are not interchangeable with
those host identities. Pin the exact model and its effective inference behavior
before comparing harnesses. Add another model as a new study.

## What is held fixed

Every study pins weights, tokenizer, chat template, sampling configuration and
inference runtime. It also pins tool semantics, capabilities, OS isolation,
each task's input and starting files, independent checks, per-execution limits,
the editor model/configuration, and each harness's revision and base settings.
The intended harness instructions differ between conditions; the task and
permissions do not. A new model, seed, tool grant, task or budget requires a new
study identity. Current campaign authorization does not include different-seed
replications.

The first editable surfaces are instruction text, tool guidance, memory
instructions and skill guidance. The proposal refers to content by SHA-256.
Changing tool definitions, permissions, budgets, executables, plugins or
delegation is outside this first matched comparison. Such changes would need
their own explicitly qualified comparison, not an instruction that quietly
expands the host's authority.

Each variant starts from the pinned base. Both proposals use only baseline
behavior; composition requires both probe receipts. Follow-up runs use the
same frozen composed recipe. Starting the next task from its base avoids
silently carrying a whole task-specific configuration into unrelated work.
An evidence-supported library of reusable components is a later integration;
this module does not yet retrieve or adopt such a library automatically.

## Behavior is visible; protected grading is not

The editor receives observed assistant actions, tool calls and results, usage
and original receipt identities. `editor-view` does not include independent
grades, check descriptions, expected answers, future executions or held-out
observations. These observations are untrusted task data, not instructions
granting access. Executor-run tests are part of observable behavior; the sealed
independent checker is separate.

The host must also keep grader files, protected questions/answers and other
harnesses' private runs outside the editor/executor boundary. A JSON projection
alone cannot prevent a process from reading another accessible file. The
operator must qualify this containment rather than adopting an upstream
unrestricted network or sandbox configuration.

## Transfer, retention and reporting

Four executions investigate the development task. For each additional unseen
transfer or retention case, run the baseline and composed configurations: two
more executions. Freeze those cases before editing. Do not rewrite the recipe
from their answers. An example with one development task, one transfer case,
one retention case and four harnesses has **32 task executions**, plus at least
12 editor sessions.

A bounded transfer screen requires all planned evidence, compatible host
qualification, a development gain, a passing composed development result,
passing transfer checks, no lost previously passed check and at least one
previously passed retention check. Missing follow-ups or no prior retention
success cannot satisfy the screen. This screen is not the separate S³ formal
mastery gate and never deploys a model or harness.

Report individual gained and lost checks. A higher total cannot conceal a
regression. Report which instruction surfaces changed across harnesses, but do
not interpret a shared surface name as proof of the same implementation or
cause. The current report exposes each unit's surfaces and paired outcomes;
cross-harness statistical conclusions need actual matched runs and appropriate
uncertainty. Four executions are too few to estimate sampling variance.

Task usage and proposer/composer usage have separate totals. Unknown usage
remains explicitly unknown. GPU allocation-hours come from PCC's actual lease
accounting, not by multiplying these task wall times; a shared serving process
and concurrent callers need accounting that avoids double charging. Grading
and reflection costs must also be recorded when those stages are connected.

## Operator interface and evidence contract

Run on an authorized development host with S³ on the Python path:

```sh
python3 -m sss study harness plan --spec private-study.json
python3 -m sss study harness editor-view --spec private-study.json \
  --evidence private-evidence.json --harness bw --task repair \
  --condition general_probe
python3 -m sss study harness report --spec private-study.json \
  --evidence private-evidence.json
```

These commands only read local inputs and print JSON. They perform no inference
or work submission. An uncertain operation must be reconciled by its original
host ID; reissuing the four-run plan is not a retry policy.

The specification has `schema: 1`, a `name`, and `evidence_kind` set to either
`host_observed` or `synthetic_contract`. Its remaining fields are:

- `model`: `weights_sha256`, `tokenizer_sha256`, `template_sha256`,
  `sampling_sha256`, `runtime_sha256`.
- `environment`: `capabilities_sha256`, `isolation_sha256`, `tools_sha256`.
- `budget`: positive `model_calls`, `input_tokens`, `output_tokens`,
  `tool_calls`, `wall_seconds` limits for each execution.
- `editor`: `model_sha256`, `configuration_sha256`.
- `harnesses`: entries with `id`, `revision`, `base_sha256`, `transport`,
  `adapter_revision`, and `qualification_sha256` (null means unqualified).
- `tasks`: entries with `id`, one `development` case and `transfer`/`retention`
  case lists. Each case has `id`, `input_sha256`, `fixture_sha256`,
  `checker_sha256`, and exact `check_ids`. No answers belong in this manifest.

`plan` supplies stable execution IDs for those conditions. An evidence bundle
has `schema`, `study_sha256`, `variants`, `runs`, `grades`, and `traces`. A run
binds its original operation/receipt, normalized behavior trace, final artifact,
observed model/environment/harness/task/budget and applied configuration. Its
outcome is `complete`, `infrastructure_error` or `uncertain`; wrong answers are
independent grades for a completed execution. Grades bind the original receipt
and artifact to the frozen checker and exact Boolean check results. Variants
bind the earlier execution receipts and traces, base, allowed content changes,
editor identity and actual editor usage. See
[`harness_compare.py`](../sss/studies/harness_compare.py) for strict fields and
[`test_harness_compare.py`](../sss_tests/test_harness_compare.py) for a complete,
explicitly synthetic bundle.

## Qualification work before the first live matrix

1. Install and pin the actual CLIs in owned environments. Confirm effective
   model selection, tool calls/results, continuation behavior, usage and errors
   against the same PCC-served Wen. Do not substitute a cloud model silently.
2. Qualify each host's OS/tool boundary and original receipt exporter. Preserve
   the original host ledger and process identity. Record differences that
   cannot be matched; do not hide them behind a common model name.
3. Connect a bounded proposer/composer using the behavior-only view. Store exact
   proposed content, its hashes, calls and observed costs. Install the proposal
   through each host's supported configuration surface.
4. Run one original file-repair task through the four conditions, then its
   frozen transfer and retention cases. Add read/edit/recovery, state tracking
   and research tasks as the host qualifications permit.
5. Publish aggregate outcomes and limitations. Keep private traces and protected
   checks private. Weight-training studies remain a separate axis.

Codex requires a verified provider setup, not a guessed endpoint.
[Official provider configuration](https://learn.chatgpt.com/docs/config-file/config-advanced#custom-model-providers)
documents the base URL, wire API and authentication settings. The reviewed
Harness² Codex bridge targets Vertex through LiteLLM; it is not an already
qualified Wen/PCC bridge. No such bridge has been added by this increment.
