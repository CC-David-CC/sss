# Turn a learning recommendation into an exact local parent

S³ recommends which measured candidate to keep working from. PCC resolves its
actual weights, adapter and optimizer files. BW submits tasks and training
intent under its existing ledger and operation IDs. These remain separate roles.

The new optional `sss_integration.resolve_parent` command joins the first two
steps. It recomputes the proposal from the original baseline, parent and
candidate evaluations; the saved proposal must match exactly. It then asks
PCC's actual owner-side resolver to check the selected native version and files.
A changed proposal cannot silently select another hat, even if someone recomputes
its unkeyed content hash.

```bash
python -m sss_integration.resolve_parent \
  --pcc-root /owned/PCC \
  --proposal /owned/next-block.json \
  --baseline /owned/original/result.json \
  --parent /owned/parent/result.json \
  --candidate /owned/candidate/result.json \
  --version /owned/native-run/versions/CANDIDATE_SHA.json \
  --profile /owned/qualified-dense-template.json \
  --artifact-root /owned --state-policy fresh \
  --output /owned/new-resolution-private.json
```

Run this on the artifact host, with the inspected source checkouts and owned
paths. LoRA additionally needs `--base-model`. A saved verified milestone can
be selected with `--checkpoint`; there is no guessed-path or model-transfer
fallback. For exact optimizer continuation use `--state-policy resume` and the
same ordered native example array in `--examples`. A new lesson block deliberately
uses fresh moments on the learned weights. It does not claim old moments were
continued across a changed dataset.

The private receipt retains the proposal identity, all three evaluation hashes,
the exact PCC reference and native artifacts, and the source identities used.
It supplies no execution authority and makes no training or promotion request.
PCC still owns numerical qualification, resources, native admission and output
registration. Read the [PCC contract](https://github.com/CC-David-CC/Private_Context_COW/blob/feat/native-learning-curves-20261024/docs/RESOLVING-TRAINING-PARENTS.md)
for the supported dense ordinary-Llama/F32 path and its explicit limits.

## Continue through an existing registered job

For a candidate already registered by PCC's training service, use its real
parent job ID and pin the resolved native artifact with
`--expected-parent-sha256` in BW or COW. That scalar is the trained full-model
hash in full mode, or the adapter hash in LoRA mode. It carries no server paths.
PCC refuses a mismatch before queuing and rechecks the parent before work.

Choosing the working parent is separate from choosing lessons and an optimizer.
Generate fresh owned practice for repair and forward groups, independently
verify demonstrations and proposed checks, retain mixed review, and keep
protected evaluation answers out of training. Select the already authorized
resource window and an explicit recipe. A rejected release gate does not erase
a useful working candidate; the evidence and repair requirements stay visible.

An offline native sweep is not automatically a training-service job. Do not
invent a `parent-job-id` from its directory name. The operator must use its
existing offline executor, or a separately authorized registration workflow.
Automatic registration/import and durable unattended multi-round execution
remain unfinished. This command closes identity resolution, not that entire loop.

## Repeatable checks

```bash
python -m sss_integration.parent_resolution_cpu \
  --pcc-root /owned/PCC --bw-root /owned/BranchWrite \
  --executable /owned/cpu-native/pcc-native-train \
  --output /owned/new-parent-binding-proof
```

This optional Linux check uses generated tiny ordinary-Llama weights and actual
native CPU updates, PCC HTTP, and both CLIs. Six real jobs establish correct
parent binding, refused wrong hashes, unchanged accepted-operation retries,
recomputed S³ proposal selection and refusal of an altered proposal. Its
semantic scores are explicitly injected to exercise the keep/repair decision;
they are not model evaluation results. Its numeric teaching fixture is owned
and host-checked, with no spontaneous language-model failure claimed.

The core remains importable without PCC, BW, NumPy, a GPU or a network. This
optional adapter verifies the selected source checkout, refuses cached helpers
from another checkout, and preserves its original input files. A resolution
file contains private paths and must not be published as a raw public report.

[The next-block planner](NEXT-SKILL-BLOCK.md), [check sensitivity](CHECK-SENSITIVITY.md)
and [measured MiniCPM curves](COW-SHARED-ROOT-LEARNING.md) cover different evidence:
decision machinery, strength of proposed checks, and actual learned behavior.


[Six real native API/CLI jobs](../validation/parent-binding-20261025-ay/cli-integration.json)
and [regression/source receipts](../validation/parent-binding-20261025-ay/checks.json)
record the checked mechanics. PCC separately records actual saved MiniCPM
update-16 resolution after temporary-cache retirement. The 68-update comparison,
broader behavioral acceptance, registered LoRA adaptive-optimizer policies and
unattended multi-round execution remain separate unfinished work.
