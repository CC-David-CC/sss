# Evaluate through the same COW engine used by BW

S³ can now opt into PCC/COW's existing consumed-request path for the frozen
direct-answer evaluator. The independent fresh-context oracle remains available
as the numerical reference. This is a connection to existing COW machinery,
not a new cache, sampler, model server, or workflow runtime.

| Component | Responsibility |
| --- | --- |
| S³ | Cases, protected splits, exact checkers, learning/forgetting comparisons |
| BW | Task execution, permissions, lessons and workflow receipts |
| PCC/COW | Immutable model identity, native inference/backprop, contexts, controllers, snapshots and GPU ownership |

BW reaches COW through its existing client and coordinator. S³'s optional local
adapter reaches `BranchingModel.run_greedy_request` directly. For dense MiniCPM,
that method delegates to the same consumed sampled/state request implementation
used by COW's serving path. Evaluation does not require a BW task ledger, but
it does exercise the engine that ledger's model calls use.

## What changes

The correctness oracle loads weights once, then creates a new context and
recomputes the entire prefix for every predicted token. The COW path loads
weights once per assessment, consumes each case's prefix once, restores that
owned prefix checkpoint, and keeps one native request alive while consuming
each generated token. Native COW selection avoids returning a full vocabulary
vector to Python for every output token.

Each independent benchmark case evicts its rebuildable RAM materializations
after completion. Canonical history, controller and response evidence remain.
This bounds memory and prevents a prior case's tail from becoming the next
case's context. It does not disable BW's normal retained-context workflows.
A changed model requires a new model-bound COW profile and session; an old
model's KV state must never be reused for newly trained weights.

## Run it

Use a real PCC checkout, its existing dense-profile preparer, an independently
qualified native build, and the same pinned cases, tokenizer, checker, model
and generation policy as the reference assessment. The initial real GPU proof
uses MiniCPM5-2B F32, a 512-token context/batch, greedy selection and stop IDs
`1 130073`. This does not certify other models or long contexts.

The existing evaluator adds two options:

```sh
python -m sss_integration.optimizer_evaluate \
  --execution-path cow --cow-profile /absolute/path/to/profile.json \
  --pcc-root /absolute/path/to/PCC \
  --cases /absolute/path/to/pinned-cases.json \
  --evaluation-id EVALUATION_SHA256 \
  --checker-implementation-id CHECKER_SHA256 \
  --model /absolute/path/to/model.gguf --model-sha256 MODEL_SHA256 \
  --oracle /absolute/path/to/llama-dense-fresh-oracle \
  --runtime-proof /absolute/path/to/qualified-build.json \
  --output /absolute/path/to/new-assessment \
  --gpu-uuid GPU_UUID --context-tokens 512 --batch-tokens 512 \
  --maximum-tokens 64 --stop-token-ids 1 130073 \
  --minimum-free-mib 16000 --maximum-initial-utilization 100
```

Choose admission limits for the host; `100` permits shared-GPU contention.
The COW adapter acquires PCC's existing per-GPU lock and rechecks free memory
before loading. Failures are infrastructure outcomes, not zero model scores,
and no failed request is automatically retried.

Without `--execution-path cow`, the fresh reference remains the default.
Do not edit a live evaluator snapshot to switch paths. Freeze a new assessment
and protocol amendment, retain the old outcome and establish a baseline for
the new runtime before interpreting learning or forgetting.

## Identity, counters and evidence

The intent stores the complete model-bound COW profile and its hash, including
physical GPU placement and the native execution-profile identity. The S³
runtime identity records the common code, native build and numerical policy
independently of candidate weights and physical placement. Thus different
candidates can be compared under one implementation without losing their
exact model or placement records. A changed math policy changes runtime identity.

COW consumes every sampled token, including EOS or the final length-limited
token, before publishing its output snapshot. The fresh reference does not
consume its final sample. Accordingly, COW's counters report actual prefix
and decode work rather than pretending to have the oracle's work schedule.
The case record retains the original COW receipt, snapshot IDs, stop reason,
sampled IDs and counter deltas. Neither path trains on evaluation cases.

## Evidence and current limits

The first shared-A100 probe passed 18 full-vocabulary comparisons on two owned
practice prefixes and eight continuation tokens per prefix. Maximum error was
`0.00007677078247070312`; worst RMS error was `0.000015165375517566687`.
Every next-token choice matched within the predeclared `0.0002` maximum and
`0.00005` RMS bounds. Saved-state restoration was bit-exact, and repeated
canonical COW requests returned identical token sequences.

The small forward-work timing included a COW restore/append check: fresh
contexts took 4.65/3.36 seconds; COW took 0.66/0.70 seconds. This is not the
end-to-end training-loop speedup. Other users were active on the shared GPU.
Full 864-case assessments of the original model and AdamW update 1 are being
measured separately, with per-case token and score comparisons. No aggregate
answer equivalence or full-run speedup is claimed from the small probe alone.

The first source-only full-assessment package omitted the curriculum catalog
and failed before inference. Its failure is retained; the corrected package
includes the catalog and verifies the original checker identity before GPU use.

This pathway currently accepts the existing dense MiniCPM profile. The dense
profile still rejects attached LoRA adapters; direct-adapter serving and merged
GGUF equivalence have separate qualification evidence. Legacy skill-guard
evaluators and other harnesses have not all been migrated by this change.

PCC's implementation and numerical evidence are described in
[COW-EVALUATION.md](https://github.com/CC-David-CC/Private_Context_COW/blob/feat/native-learning-curves-20261024/docs/COW-EVALUATION.md).
