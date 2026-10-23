# Integrating SÂ³

The SÂ³ core takes a tree, completed check results, a native-training callback and
host-owned lesson readers. It imports no BW/PCC code. Optional modules under
`sss.adapters` provide specific connections. They do not grant tools or create a
second task ledger.

For development, install SÂ³ into the same Python environment as the matching
host checkout:

```sh
python -m pip install -e /path/to/sss
```

BW's `/skills` can show the broad SÂ³ map. `branchwrite lesson skills` and the
standard COW client's `lesson skills` inspect a server's configured active tree.
Those are different scopes: the broad catalog is not a model qualification.

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

From the SÂ³ checkout with the matching BW/PCC source available:

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
regression and recovery; it is not fresh language-model inference. A separate
`sss_integration.lesson_native_cpu` harness covers the earlier one-example,
batch, LoRA/full continuation and reload workflow. Both refuse old output paths.

## Host-trace grading

`sss.suites.tool_use.grade` checks completed host observations and actual final
files. An adapter must validate its canonical receipts before calling it. A
dictionary supplied by a model is not execution evidence. Unknown effects or
unsettled infrastructure produce `unavailable`, not a false pass or a new model
training example. These graders do not replace BW's acceptance/runtime checks.
