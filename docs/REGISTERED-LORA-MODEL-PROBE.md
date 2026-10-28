# Qualify the registered LoRA pathway on MiniCPM

The optional `sss_integration.registered_lora_model` probe exercises S³,
PCC's existing authenticated lesson/job service, BW's actual CLI, COW's actual
CLI and the native AdamW LoRA engine. It performs three service jobs: one
update, one resumed update, and a separate two-update control. All use the same
checked example and deterministic native initialization. This is a mechanics
qualification, not a held-out learning experiment or a model release decision.

S³'s existing foundation generator, independent checker and PCC renderer supply
the lesson. The probe does not invent another arithmetic grader, tokenizer,
template, optimizer, task ledger or GPU scheduler. It uses synthetic owned
practice and explicitly does not describe that example as an observed LLM failure.

## Owner setup

Use authorized Linux hardware and the owned PCC, BW and S³ checkouts. Keep
model files local. The probe currently requires a MiniCPM5 GGUF routed through
the ordinary-Llama backend, plus an already-qualified native training executable.
NumPy is needed for the final saved-tensor comparison, not S³ core imports.

Prepare an existing COW profile for the exact original model, and a dedicated
PCC service configuration as described in the
[registered LoRA guide](https://github.com/CC-David-CC/Private_Context_COW/blob/feat/native-learning-curves-20261024/docs/REGISTERED-LORA-ADAMW.md).
The probe uses that profile to bind the model contract and actual tokenizer;
it does not start inference or qualify the profile's inference placement.

The service configuration must have:

- A new `directory` equal to `OUTPUT/service`, inside the new probe directory.
- The exact model path/hash, qualified native executable, physical GPU UUID,
  logical CUDA device, memory reserves and hard execution deadline.
- `sequence_profile: "dense-llama-short-v1"`, the qualified memory profile,
  `max_tokens` no greater than 512 and `max_steps` at least two.
- Exactly one schema-2 fresh LoRA AdamW policy and one matching resume policy.
  Rank, rate and optimizer settings match. Both phase-time budgets are null.
  The policies' IDs are computed from their exact descriptors.
- No legacy multi-round `skill_guard_config` wrapper.

Do not use a running study's service store or change its policies. PCC's existing
GPU leases remain authoritative. If an owner scheduler also uses placement
claims, coordinate through those claims before starting the GPU phase; apparent
free VRAM is not proof that an owned GPU slot is available.

## Prepare without allocating a GPU

From the S³ checkout:

```bash
python -m sss_integration.registered_lora_model prepare \
  --pcc-root /owned/PCC --bw-root /owned/BranchWrite \
  --service-config /owned/lora-probe-config.json \
  --profile /owned/original-cow-profile.json --output /owned/lora-probe
```

This uses S³'s existing practice-pack verification and exact PCC chat rendering,
then admits the lessons through PCC. It selects one checked carry-addition
practice example. Actual serving tokens must agree with the training renderer;
the answer and its template terminator are supervised, while the input and
generation header are not. No generated thinking span is attested.

`prepared-private.json` pins the configuration, profile, model, executable,
source files, policy IDs and selected lesson. The existing practice helper also
writes `practice/finished-training-examples.txt` with the checked question/answer
and explicit synthetic-practice provenance. Keep these private; no protected
development question or answer becomes training data.

## Execute and compare

With the intended resource slot admitted, run the same command with `run`:

```bash
python -m sss_integration.registered_lora_model run \
  --pcc-root /owned/PCC --bw-root /owned/BranchWrite \
  --service-config /owned/lora-probe-config.json \
  --profile /owned/original-cow-profile.json --output /owned/lora-probe
```

The probe refuses changed prepared inputs before dispatch. It records a run
intent before sending jobs and starts an authenticated loopback service with an
ephemeral key supplied to its real CLI clients through the environment.

BW submits the checked lesson with `--train-now` for one update. COW selects the
same lesson and exact adapter parent for one resumed update, retaining moments
and cursor. A separate COW request trains two updates from the original base.
The saved adapter tensors and every optimizer moment must match exactly.
The resumed global step and example cursor must both be two. Original operation
IDs are retried to check that no additional native updates occur. The base
model must remain unchanged and all reported gradients must be finite.

`result.json` contains reduced identities, declared recipe, counters and native
batch losses. Private service operation/run records and client logs retain
the original evidence. No GGUF is merged, quantized, uploaded or promoted.
Native batch-loss changes do not establish generalization, retention, useful
tool behavior or broad learning. Those need independent S³ assessments.

## Recover without repeating uncertain work

The probe will not restart when its run-intent file already exists. Inspect the
original process identity and PCC operations before doing anything else. The
jobs are named `first-train`, `resumed` and `uninterrupted`. Read their original
status and native child receipts; an SSH timeout is not evidence that training
stopped. Do not create new IDs or reset moments to work around uncertainty.

A resource refusal before the probe's run intent and before any training job
was created can be rescheduled after verifying the original admission owner is
terminal. Preserve that refusal separately. It is not a model failure or a
reason to relax a numerical comparison.

This probe is not the durable multi-round learning coordinator. That supported
path still needs measured failure capture, next-block decisions, resource and
child reconciliation, broader evaluation, private preservation and repeated
rounds through the existing PCC/BW records.


## Measured A100 result

The probe passed on the original F16 MiniCPM5-2B base and previously qualified
native engine, using rank 16, AdamW at 1e-4 and one rendered 59-token checked
practice example with three supervised targets. All three real HTTP/native jobs
completed. The resumed and uninterrupted final adapter files share SHA-256
`b8b8776b880f9a65056a89a79484f5f42ac3acec6ab0de5d667398b54d14e9b0`;
the optimizer files share SHA-256
`5f16ea7016c069ac81644c927cc8206e7efd0d2aa05e7a31dff1f3aea2e685c7`.
This is a comparison of complete saved bytes, in addition to inspected tensors.

Training loss on that practice example moved 7.7261 → 2.4041 → 0.08077. That
says nothing by itself about unrelated questions or forgetting. Original client
operation retries did not train again, and rerunning the whole probe was refused
before service startup with all original operation hashes unchanged.

One initial placement refusal happened before dispatch; it was preserved and
rescheduled only after confirming the original admission owner was terminal
and no job existed. The successful one-GPU placement reservation lasted 182.8
seconds, or 0.0508 allocation GPU-hours. That includes I/O, CPU comparison and
shared contention; it is not a training-kernel timing comparison. Probe owners
terminated after completion, with no remaining probe worker.

[Integration identities and native results](../validation/registered-lora-model-20261025-ba/integration.json)
and [source/recovery receipts](../validation/registered-lora-model-20261025-ba/checks.json)
contain reduced evidence without private teaching text, model files or service
keys. The frozen 68-update study and its settings were left unchanged.


The [frozen GPU-executed probe source](../validation/registered-lora-model-20261025-ba/executed-probe.txt)
is retained separately from the released helper. After GPU completion, its
numeric array comparison was tightened to require finite values and identical
stored bytes, dtype and shape; this distinguishes positive from negative zero.
The stricter helper passed a [CPU recheck on the unchanged actual artifacts](../validation/registered-lora-model-20261025-ba/byte-comparison.json),
without more native updates. Two distinguishing comparison tests, thirteen
learning-policy regression tests and the stdlib-only optional-import check
also passed; see [release checks](../validation/registered-lora-model-20261025-ba/release-checks.json).
The original GPU result already included matching whole-file hashes. This
comparison refinement changes no training recipe, gradient or saved weight.
