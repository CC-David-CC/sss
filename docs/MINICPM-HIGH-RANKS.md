# MiniCPM: walking the LoRA ranks

**Work in progress. Rank-32 AdamW reached 256/864 at update 2; the extended curves are not complete.**

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
| 32 | 54,476,800 | Update 3: 284/864 correct; 816/864 naturally finished | Pending |
| 128 | 217,907,200 | Pending | Pending |
| 2048 | 3,486,515,200 | Pending | Pending |
| 4096 | 6,973,030,400 | Update 1 saved; export and assessment pending | Update 1 saved; export and assessment pending |

Snapshot: 2026-10-27. This table records the last inspected state, not a live
monitor. AdamW rank 4096 was dispatched on A100 GPUs 2 and 3; factorwise Muon
on GPUs 0 and 7. These are separate arms, not repeated runs. Both optimizers passed
generated tiny-model two-GPU continuation tests and actual-model persistent
memory admission. Both completed their first native update and verified saved
adapter and optimizer-state artifacts. Their export and assessment checks remain
pending. Execution-graph allocation, saved artifacts and evaluation are separate
gates; persistent admission alone does not establish successful training.

Rank-32 AdamW completed its first update on the separate llm-60 worker. Every
merged weight passed the independent FP64 audit (maximum error 8.98e-8).
Adapter-versus-merged logits on one original practice input differed by
0.000118, within the unchanged 0.0002 bound; loss differed by 0.0000055.
The [export-check receipt](results/minicpm-highrank-20261027/rank32-update001-merge.json)
records that limited scope. Its frozen 864-question assessment completed through
the existing PCC/COW shared-prefix path: **215 correct, 775 naturally finished**.
The [assessment receipt](results/minicpm-highrank-20261027/rank32-update001.json)
includes skill/gate breakdowns and provenance hashes. This is update 1 after 27
practice presentations, not an update-68 endpoint. Its home runtime is recorded
separately from the A100 reference runtimes; the reference table above therefore
does not establish an optimizer-only or rank-only causal effect.

The bounded continuation pilot then resumed the exact adapter, moments and
practice cursor for update 2, exported and checked the result, and completed the
same assessment. It scored **256 correct, 788 naturally finished**, after 54
practice presentations. Relative to update 1, **44 answers became correct and
3 became incorrect**: a net gain of 41, with forgetting measured rather than
hidden by the total. The [update-2 receipt](results/minicpm-highrank-20261027/rank32-update002.json)
includes that paired breakdown. Both assessments used the same recorded home
runtime. The pilot stopped at its declared update-2 boundary; a longer run still
requires the rolling artifact-retention path.

Update 3 then reached **284 correct, 816 naturally finished**, after 81 practice
presentations. Compared with update 2, **34 answers became correct and 6 became
incorrect**; natural completion gained 31 cases and lost 3. The
[update-3 receipt](results/minicpm-highrank-20261027/rank32-update003.json)
binds the same frozen assessment and home runtime. The bounded pilot stopped
at update 3. This is continuing development evidence, not a release acceptance.

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
reaches every targeted matrix's full rank capacity. Rank 4096 does not increase the maximum rank of the merged weight matrix,
but its additional factor dimensions change the optimization geometry. Factorwise
Muon orthogonalizes updates to the larger A and B factors separately; AdamW
uses coordinatewise adaptive updates without that orthogonalization. Extra factor
dimensions can therefore affect both regimens differently even after matrix rank
capacity saturates. Comparing these effects on learning and forgetting is a central
purpose of the high-rank study. Better performance remains an empirical question.

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
