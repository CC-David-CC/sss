# Integrating S³

The S³ core takes a tree, completed check results, a native-training callback and
host-owned lesson readers. It imports no BW/PCC code. Optional modules under
`sss.adapters` provide specific connections. They do not grant tools or create a
second task ledger.

For development, install S³ into the same Python environment as the matching
host checkout:

```sh
python -m pip install -e /path/to/sss
```

BW's `/skills` can show the broad S³ map. `branchwrite lesson skills` and the
standard COW client's `lesson skills` inspect a server's configured active tree.
Those are different scopes: the broad catalog is not a model qualification.

An active case can name a generic checker contract instead of arithmetic fields:

```json
{"id":"SHA256_OF_PROMPT","prompt":"Read the assigned file","checker":{"name":"host-tool-trace","version":1,"case_id":"files.read"}}
```

The host registers the evaluator implementation and supplies validated results.
The JSON does not import code, choose an executable or grant a tool. This keeps
the tree usable for tool, admin and coding suites as their adapters are added.
The built-in arithmetic adapter explicitly rejects other checker contracts.

## Owner-configured PCC guard

Prepare the starter practice tree before starting a PCC service that owns the
same lesson store. The model profile must identify the exact training tokenizer.

```sh
sss init-pcc --training-config /private/training.json \
  --profile /private/profile.json --output /private/skills.json
```

This initializes owned, independently checked retention practice. The associated
negative controls are labelled constructed fixtures, not spontaneous model
failures. It does not start training. Training/evaluation prompts are disjoint;
no example is silently truncated to fit an owner token budget.

Add an owner-only `skill_guard_config` path to PCC's optional training config.
That file has these fields:

```json
{
  "schema": 1,
  "tree": "/private/skills.json",
  "oracle": "/private/native-build/qwen35-mixed-oracle",
  "evaluation_gpu_uuid": "OWNER_SELECTED_PHYSICAL_GPU_UUID",
  "round_examples": 32,
  "max_rounds": 4,
  "focus_fraction": 0.5
}
```

The current built-in evaluator covers arithmetic expressions on a supported
dense Wen/Qwen3.5 model. Other domains need their own independent evaluator;
adding a catalog name does not implement it. The evaluator respects account GPU
leases and passes the host worker lease into native children. No live server is
evicted and no candidate replaces existing COW contexts.

After a real BW task failed, was corrected and passed checks:

```text
/lesson create --prompt-file /private/input.txt --completion-file /private/correction.txt --skill python.arithmetic.ceil --operation-id ceiling-lesson --train-now --skill-guard --batch-size 8 --steps 16
```

The caller explicitly requests `--skill-guard`. Its frozen policy ID is recorded
in the original request. Here a 32-example round uses four updates, so 16 steps
allow at most four rounds, within the owner's limit. The budget is a ceiling;
qualification may stop earlier. Every original selected lesson is consumed in
the first round. Select at most the focused share of new lessons per job.

Ordinary unguarded jobs keep their earlier exact-step behavior. Reconciliation
uses the original operation, selection and policy; changing the server tree
does not turn a retry into a new training request. Parent hats must have
qualified under the same guard policy. A new tree requires deliberate baseline
qualification, not a silent change to an old candidate's meaning.

## Reproduce integration mechanics on CPU

From the S³ checkout with the matching BW/PCC source available:

```sh
PYTHONPATH=/path/to/PCC:/path/to/BW python -m unittest discover \
  -s sss_integration -p 'test_*.py'
python -m sss_integration.skill_native_cpu \
  --bw-root /path/to/BW --pcc-root /path/to/PCC \
  --native-executable /path/to/cpu-build/pcc-native-train \
  --workdir /private/new-skill-proof
```

The harness uses real BW checks, both clients, authenticated HTTP, native CPU
updates, saved hats and continuation. The evaluator deliberately injects a
regression and recovery; it is not fresh language-model inference. The
`sss_integration.lesson_native_cpu` harness covers one-example and batch updates,
LoRA/full continuation and reload, plus five S³ response lessons through BW and PCC:
direct answer, checked-reasoning answer, format-only, direct composed, and
checked-reasoning composed. It verifies PCC's stored tokens, targets and loss mask,
then checks the exact same mask in the native request before running one CPU update
per policy. It uses a generated tiny fixture, keeps the base unchanged, promotes no
candidate, and says nothing about language quality. Both harnesses refuse old output
paths.

## Independently re-check a BW failure/correction pair

BW's `capture-failure` and `capture-correction` commands preserve the private
workflow evidence and exact files. Their receipt explicitly does not claim S³
verification or training approval. The optional S³ adapter below validates both
capture IDs and the correction's link to that failure, then runs an S³-owned
registered checker over the exact captured source bytes in a disposable Linux
namespace. Its first paired fixture is `python.double`.

Run from the S³ checkout, with the matching BW checkout importable:

```sh
PYTHONPATH=/path/to/BW python -m sss_integration.bw_capture_verify \
  --failure /private/captures/failure \
  --failure-capture-id SHA256_FROM_BW_FAILURE_RECEIPT \
  --correction /private/captures/correction \
  --correction-capture-id SHA256_FROM_BW_CORRECTION_RECEIPT \
  --case python.double
```

The command prints a sanitized JSON receipt. `verified` means the captured
failure fails and the captured correction passes the independent S³ checker.
`mismatch`, `unavailable` and `refused` are separate outcomes; none authorizes
training. The receipt contains capture IDs, source hashes, checker identity and
verdict hashes, but no captured prompt, completion or file contents. Keep BW
archives private. This proof creates no lesson and dispatches no training job;
an owner or authorized agent must still choose a separate practice example and
submit it through the established BW/PCC learning path.

Qualify the controlled BW/S³ handoff on an authorized Linux host with bubblewrap:

```sh
BW_ROOT=/path/to/BW PYTHONPATH=/path/to/BW python -m unittest \
  sss_integration.test_bw_capture_verify
```

The test creates a controlled failed check and correction through BW's real
ledger and capture code. It proves the cross-project mechanics, not a model's
spontaneous failure, lesson quality or learning. The [sanitized test record](../validation/learning-program-20261024/bw-capture-oracle-machinery.json)
and [oracle receipt](../validation/learning-program-20261024/bw-capture-oracle-receipt.json)
contain only hashes and verdict metadata; the private BW archives are not included.

### Public shell task command adapter

For visible `shell.failure_status` and `shell.quoted_filename`
tooling-qualification tasks, S³ can materialize the starting script and
relative test inputs that BW's isolated workspace needs:

```python
from sss_integration.bw_task_adapter import prepare_public_bw_task

task = prepare_public_bw_task('shell.failure_status', '/private/new-empty-project')
# Pass task['task'], task['read_paths'], task['edit_paths'], and
# [task['test_command']] to BW's existing coding CLI.
```

These are public development fixtures, not hidden benchmarks. Each command is
visible to the model and runs entirely inside the BW workspace; commands contain
no host-specific paths. A command receipt proves BW ran that check, not that the
code is correct. Validate the captured source with the matching independent S³
host checker before reporting a pass, creating a lesson, or training. Do not use
these visible fixtures as held-out scores. Contract tests compare each exact
command against both the broken and reference script; run them on a Linux host.

## Audit native completion recovery separately

PCC owns recovery of the original native job, and BW provides the person/agent
owner commands. S³ has a small optional auditor for their saved qualification
records. It reads the private receipts and local artifacts, then writes only a
sanitized summary. It never starts PCC, BW, training, inference, or recovery.

```sh
python -m sss_integration.native_completion_recovery \
  --qualification-root /private/new-native-recovery-qualification \
  --output /private/new-native-recovery-qualification/sss-receipt.json
```

The root must contain the exact qualification layout emitted by the PCC/BW
recovery harness, including its private event record, native/reload exit
receipts, completion gate, job store, base fixture, deliberate-fault receipt,
and recovery-dispatch guard receipt. The output must be a new file; overwrite
is refused. `PASS` means the saved records agree on one original full-AdamW
CPU update, successful reload, deliberate service exit, same-job adoption and
reconciliation to `candidate_pending`, with no second training dispatch or
promotion. It does not prove that the host records are independently attested,
that MiniCPM/Wen learned anything, or that a candidate should be accepted.

Missing evidence returns `HOLD` (exit 2). Inconsistent, altered or malformed
evidence returns `FAIL` (exit 1). Neither result is a model-quality judgment.
Raw event logs, operation IDs, service credentials and model files remain
private. The [published S³ receipt](../validation/learning-program-20261024/native-completion-recovery-machinery.json)
is the sanitized result from one tiny synthetic CPU qualification. This audit
is independent of the frozen 68-update optimizer comparison.

Run its synthetic contract tests without BW, PCC, NumPy, a model or a GPU:

```sh
python -m unittest sss_integration.test_native_completion_recovery
```

These tests verify the receipt checks and tamper refusals. They are not another
native model run.

## Host-trace grading

`sss.suites.tool_use.grade` checks completed host observations and actual final
files. An adapter must validate its canonical receipts before calling it. A
dictionary supplied by a model is not execution evidence. Unknown effects or
unsettled infrastructure produce `unavailable`, not a false pass or a new model
training example. These graders do not replace BW's acceptance/runtime checks.
