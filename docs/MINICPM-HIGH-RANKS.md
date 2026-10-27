# MiniCPM: walking the LoRA ranks

**Work in progress. No high-rank capability score is available yet.**

Can a larger adapter preserve more useful learning, and how do AdamW and
factorwise Muon differ as adapter rank grows? This extension has its own branch
and report. The [original frozen study](https://github.com/CC-David-CC/sss/blob/feat/minicpm-update-curves-20261026/docs/FINAL-CHECKPOINT-PRECISION.md)
continues independently; its remaining results do not depend on this extension.

## The small reference set

These are measured update-68 results from the original study, all out of 864
questions. Rank 1 was the lowest-scoring and rank 16 the highest-scoring F32
endpoint among its six AdamW LoRA ranks. They are selected examples, not a
replacement for the complete results. Full AdamW and standard Muon supply the
full-weight references. Ties and intermediate ranks remain in the original report.

| Original reference | F32 correct | Q4_K_M correct | Q2_K correct |
|---|---:|---:|---:|
| AdamW LoRA rank 1 | 450 | 409 | 21 |
| AdamW LoRA rank 16 | 494 | 492 | 36 |
| Full AdamW | 482 | 471 | 35 |
| Full standard Muon | 494 | 471 | 28 |

The historical original F32 model scored 59/864. Its runtime differed from the
trained-model runtime, so that historical comparison is not a matched-runtime
estimate of the training effect. The original report records that limitation.
No quantized high-rank results have been measured for this extension.

## The new arms

Each rank is planned with AdamW and factorwise Muon, once per configuration.
The comparison follows 68 updates of the same ordered practice, batch size 27,
with 1,836 practice presentations at update 68. Optimizer state and the example
cursor continue between points. There is no fixed training-time budget.

| Rank | Trainable adapter parameters | AdamW | Factorwise Muon |
|---|---:|---|---|
| 32 | 54,476,800 | Pending | Pending |
| 128 | 217,907,200 | Pending | Pending |
| 2048 | 3,486,515,200 | Pending | Pending |
| 4096 | 6,973,030,400 | First update dispatched; no completed score | Pending |

Snapshot: 2026-10-27. This table records the last inspected state, not a live
monitor. AdamW rank 4096 was dispatched on two A100s. Both optimizers passed
generated tiny-model two-GPU continuation tests and actual-model persistent
memory admission. Execution-graph allocation and the first actual update remain
separate gates; admission does not establish successful training.

AdamW starts at the original LoRA comparator rate, 1e-4. Factorwise Muon starts
with the standard full-Muon comparator's 5e-5 matrix rate and 1e-6 auxiliary
AdamW rate. These are initial comparison settings, not claimed optima. Different
parameterizations and rates make this a regimen comparison, not an isolated
optimizer-effect estimate. Any changed regimen receives a separate identity.

## What increasing rank actually means

The model contains 2,516,756,480 parameters. Its current adapter targets 295
linear matrices, including the prediction head; embeddings and normalization
weights stay frozen. Adapter parameter count is 1,702,400 times rank.

For an m-by-n matrix, rank-r factors contain r(m+n) parameters but, below
saturation, only r(m+n-r) independent degrees of freedom. Rank 2048 already
reaches every targeted matrix's full rank capacity. Rank 4096 adds redundant
factor parameters rather than more representable matrix directions. It can
still change optimization behavior; whether that helps is an experimental question.

LoRA's bilinear factors do not make its optimizer a Hessian-based second-order
method. Factorwise Muon orthogonalizes updates to A and B independently. It is
different from orthogonalizing a full dense update and then factorizing it.
Prediction-head factors retain auxiliary AdamW updates.

## How to read the forthcoming graphs

Plot completed update number against correct answers, answers gained and lost,
and natural stopping. Missing points stay missing; failed infrastructure is not
a zero capability score. Use the same protected questions and checker for the
fixed comparison. Report runtime identities and changes rather than assuming
that a shared model name establishes equivalence.

Compute time, peak memory, allocation failures and shared-server contention are
outcomes to report, not the axis used to equalize practice. Quality at equal
updates is still distinct from quality per second or per byte of optimizer state.

The broader goal is a reusable S³/BW/PCC learning loop: observe a failure,
verify a lesson, train a candidate, measure learning and forgetting, make an
explicit acceptance decision, preserve the named artifact, and repeat. This
extension informs that machinery; a better score on this repeatedly inspected
development set alone does not establish broad skill mastery or release quality.

Native implementation and qualification are maintained in
[PCC's factorwise-LoRA branch](https://github.com/CC-David-CC/Private_Context_COW/tree/feat/factorwise-muon-lora-20261027).
Its published small-rank milestone and the pending extended-rank work are
distinct. Models, optimizer states and protected response traces remain private.
