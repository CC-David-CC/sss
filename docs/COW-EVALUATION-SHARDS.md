# Independent evaluation cases, checked parallel merges

S3's frozen direct-answer evaluator supports explicit case shards. PCC/COW
still owns the model, context, consumed request and GPU lock. Each worker uses
its own COW session, output directory and pinned physical GPU. BW or an owner
script can launch these finite workers using the existing workflow authority.
S3 adds no service, model server, tool permissions or second workflow ledger.

This applies to independent, fully rendered questions. Do not split a research
episode, training update chain, shared environment or conversation into shards
unless its own protocol establishes that those units are independent.

## Assign cases

The existing `sss_integration.optimizer_evaluate` command adds:

```text
--shard-count 2 --shard-index 0
--shard-count 2 --shard-index 1
```

Use otherwise identical cases, model, checker, limits and numerical policy;
bind each COW profile to its actual GPU. See [COW-EVALUATION.md](COW-EVALUATION.md)
for the complete evaluator command. The default remains one unsharded worker.

Assignments are deterministic strides through original case order. Two workers
receive indices `0,2,4,...` and `1,3,5,...`. The partition binds the frozen
evaluation ID, every case ID, skill, gate, assignment and shard count. A worker
keeps original case indices and stream names; it never renumbers a question's
generation stream. Each shard reports `SHARD_COMPLETE`, not `COMPLETE`.

The runtime identity pins the partition implementation as well as the evaluator,
adapter, checker and native build. Worker placement stays in its full COW profile
and intent. Candidate weights and placement do not masquerade as a different
common numerical implementation.

## Merge complete evidence

Measure worker-group wall time in the owner process, from launching workers
through their completion. A completed shard is reusable evidence if another
worker fails; no failed shard or training update is automatically replayed.

```sh
python -m sss_integration.merge_evaluations \
  --cases /absolute/path/to/pinned-cases.json \
  --evaluation-id EVALUATION_SHA256 \
  --shard /absolute/path/to/shard-0/development \
  --shard /absolute/path/to/shard-1/development \
  --coordinator-wall-seconds MEASURED_GROUP_SECONDS \
  --output /absolute/path/to/new-merged-assessment
```

The output parent must already exist. The output must be separate from worker
evidence, including through filesystem aliases. The merger is CPU-only. It checks
complete coverage, unique IDs, exact skills/gates, model/runtime agreement,
aggregate counts, source pins, intents, settlements and private response files.
It copies response evidence under original indices, records hashes, and syncs
files/directories before publishing the final `COMPLETE` marker. A failure leaves
evidence and no complete result. Power-loss behavior is not separately certified.

GPU allocation seconds are the sum of the owned worker intervals. Group wall
time is the caller's measured interval, not the sum of parallel worker times.
These are different quantities. The operator remains responsible for choosing
resources and recording that measured interval truthfully.

## What the real A100 test established

Two workers on shared A100 cards 4 and 7 each evaluated 432 original MiniCPM F32
questions. The checked merge covered all 864 questions with **identical sampled
token sequences and scores** to the saved serial COW assessment: **59 correct,
415 naturally finished**.

This particular split was **slower**: the worker group took **21.8 minutes**,
compared with the earlier single-card evaluation's **19.1 minutes**. It used
**2,211 allocated GPU-seconds**, compared with **1,136** in the earlier serial
run. Other users were active and loads differed. The group timer also includes
worker preflight/admission, while the earlier evaluator timer excludes its
initial preflight hashing. This is not an isolated scaling benchmark.

The faster shard's evaluator took 937 seconds and the slower shard approximately
1,290 seconds. Equal case counts did not guarantee equal completion times.
Parallelism is therefore **opt-in**, not a claimed automatic speedup. Smaller
work units and existing COW allocation/prefix reuse are candidate next tests;
we have not deployed an adaptive scheduler or shared native context pool here.

The full 864-case run used the frozen source package recorded in its aggregate
evidence. Subsequent source/intent guards were tested against actual two-case
MiniCPM output and a CPU merge; the forward-request code is unchanged. This
distinguishes full behavior evidence from the narrower final guard smoke.

The focused 27-test run passed shard/merge, paired, execution-analysis and
adapter checks, including the shared-prefix input helper. They include missing/duplicate
cases, wrong models/runtimes/skills, bad aggregates, corrupted response evidence,
impossible timing, output aliases and deterministic merge order.

Evidence:

- [Full two-card assessment](../validation/minicpm-native-learning-20261024/cow-shards-parallel.json)
- [Final source-guard native smoke](../validation/minicpm-native-learning-20261024/cow-shards-source-guards.json)
- [Instrumented CPU profile](../validation/minicpm-native-learning-20261024/cow-shards-cpu-profile.json)

The CPU profile comes from two short instrumented requests. Hashing, file access,
model loading and state restoration were prominent there. Instrumentation and
startup dominate such a short run; its percentages must not be extrapolated to
a full 864-case assessment. It motivates a measured next experiment, not a
conclusion that all remaining time is CPU work.

Shared-root evaluation is now an explicit option described in
[COW-EVALUATION.md](COW-EVALUATION.md). It uses the original COW branching
implementation. Its new full baseline is still in progress; the two-card timing
above used independent per-question roots and must not be attributed to that
new shared-root mode.
