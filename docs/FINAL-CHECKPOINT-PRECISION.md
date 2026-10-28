# Final-checkpoint precision: all ten original training arms

Snapshot: 2026-10-27T04:18:52.370852+00:00. **All 80 model/format panels are complete**:
ten arms, eight formats, 864 questions per panel. Every endpoint is update 68
after 1,836 ordered practice presentations. The separate
[high-rank extension](https://github.com/CC-David-CC/sss/blob/feat/minicpm-highrank-20261027/docs/MINICPM-HIGH-RANKS.md)
is not part of this fixed comparison.

![All ten endpoint precision sweeps](results/minicpm-20261026/final-checkpoint-precision.png)

The original model appears at each measured precision. Its original F32
assessment was recovered and audited from existing receipts, without new
inference. That original sweep used a prior runtime: it is a historical reference,
not a matched-runtime causal estimate of training alone. Within each trained
arm, precision outcomes are paired against that arm's own F32 master.

## Correct answers out of 864

| Format | Original | Full AdamW | Standard Muon | RMS/decay Muon | Fast/refine Muon | LoRA r1 | LoRA r2 | LoRA r3 | LoRA r4 | LoRA r8 | LoRA r16 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| F32 | 59 | 482 | 494 | 495 | 480 | 450 | 479 | 475 | 493 | 492 | 494 |
| F16 | 59 | 481 | 494 | 495 | 480 | 450 | 479 | 475 | 493 | 492 | 494 |
| Q8_0 | 43 | 480 | 498 | 495 | 482 | 446 | 480 | 474 | 493 | 488 | 491 |
| Q5_K_M | 58 | 468 | 491 | 487 | 466 | 438 | 466 | 469 | 484 | 487 | 482 |
| Q4_K_M | 34 | 471 | 471 | 471 | 480 | 409 | 460 | 457 | 486 | 479 | 492 |
| Q3_K_M | 50 | 346 | 353 | 354 | 333 | 268 | 260 | 297 | 364 | 315 | 401 |
| Q2_K | 4 | 35 | 28 | 28 | 25 | 21 | 16 | 23 | 14 | 31 | 36 |
| Q1_0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

## Naturally finished responses out of 864

| Format | Original | Full AdamW | Standard Muon | RMS/decay Muon | Fast/refine Muon | LoRA r1 | LoRA r2 | LoRA r3 | LoRA r4 | LoRA r8 | LoRA r16 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| F32 | 415 | 864 | 864 | 864 | 864 | 863 | 864 | 864 | 864 | 864 | 864 |
| F16 | 415 | 864 | 864 | 864 | 864 | 863 | 864 | 864 | 864 | 864 | 864 |
| Q8_0 | 392 | 864 | 864 | 864 | 864 | 863 | 864 | 864 | 864 | 864 | 864 |
| Q5_K_M | 398 | 864 | 864 | 864 | 864 | 863 | 863 | 864 | 864 | 864 | 864 |
| Q4_K_M | 522 | 864 | 864 | 864 | 864 | 811 | 862 | 864 | 864 | 864 | 864 |
| Q3_K_M | 475 | 863 | 864 | 864 | 864 | 797 | 795 | 840 | 831 | 863 | 863 |
| Q2_K | 521 | 821 | 830 | 794 | 816 | 825 | 811 | 815 | 778 | 824 | 817 |
| Q1_0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

Every zero is measured. The 80 panels represent **69,120 scored model/question
combinations**, including existing F32 assessments reused under their exact
runtime/input checks. They do not represent 69,120 new calls by this report.
Report preparation made no model call or training update.

## ELI5

Ten students finished the same 68 practice sessions. We packed each student
into eight file sizes and asked each version the same 864 questions. All those
packing tests are now finished. The smaller files often keep much of the gain
through Q4, then lose a lot at Q3 or below. Individual results are not perfectly
smooth: standard Muon scored 494 at F32 and 498 at Q8. That does not establish
that shrinking a model generally makes it smarter.

## Master's level

Each inference format was converted directly from its own F32 master. The six
LoRA masters were merged natively in PCC and independently checked against
FP64 weight reconstruction before conversion. Full-weight arms already produce
F32 models. Existing complete F32 assessments were reused only after exact
runtime/input validation. Attached-adapter assessments were not silently
substituted for standalone merged-model assessments.

The evaluator uses PCC/COW shared-prefix reuse, greedy decoding, 512-token
context and a 64-token output limit. Exact model, runtime and checker identities,
settlement hashes and per-skill/gate transitions are retained. F16 had identical
answer and finish verdicts to F32 in 9 of ten arms; that does not claim
identical logits or response text.

Totals hide changes in both directions. Full AdamW's F16 score of 481 includes
one answer gained and two lost. Rank 16's Q4 score of 492 includes 20 gained and
22 lost. Standard Muon's Q8 score includes 6 gained and
2 lost. Those paired differences matter when deciding
what a subsequent lesson block should practice.

The full-weight update-68 scores are AdamW 482, standard Muon 494, RMS/decay
Muon 495 and fast/refine Muon 480. The one-question difference between the two
highest totals does not establish which optimizer is generally preferable.

## PhD level and limits

This study fixes update count and ordered practice exposure, not training time.
Rates, decay, adaptation and numerical/runtime paths differ by declared regimen;
this is not an optimizer-only or adaptation-only causal ablation. It contains
no independent-seed repetitions and no sealed broad-task acceptance test.
Repeatedly inspected development questions are not evidence of general skill
mastery. Update 68 is the fixed comparison endpoint, not necessarily an arm's
peak earlier checkpoint or its best model for every skill or precision.

Nearby scores do not imply behavioral equivalence. Quantization can change
correctness in either direction, and output limits affect natural completion.
These are post-training conversions. Quantization-aware training was not used;
QAT at Q4 and below remains separate follow-up work.

## Recovering slow panels without repeating completed cases

Three panels were relocated after their GPUs became heavily contended.
The continuation preserved 328 completed rank-2 Q2 cases, 257 standard-Muon
Q3 cases and 174 fast/refine Q2 cases. Only
the respective missing inputs were dispatched on another card. The original
process identity, destination leases, memory, source, weights and unchanged
numerical runtime were checked before interruption.

Existing token receipts were decoded and independently regraded. Original
hashes were checked again after completion. Each reduction requires disjoint
coverage of all 864 original case identities. No completed case or training
update was repeated during these continuations. Partial computation on an
unfinished case may have been discarded when its original worker stopped.

Original interrupted-run records remain intact. Explicit recovery pointers,
source-map hashes and result/settlement hashes identify the separate completed
continuations in the [aggregate evidence](results/minicpm-20261026/final-checkpoint-precision.json).
This does not relabel the interrupted original executions as successful ones.

Observed case times dropped from roughly 13-16 seconds under contention to
about 0.6-0.8 seconds after relocation. These are shared-load observations,
not an isolated kernel benchmark or a universal speed multiplier.

## Applied meaning

Choose a precision from its measured skill results and deployment memory needs.
Rank 1, for example, falls from 450 to 409 correct at Q4, whereas rank 16 keeps
492 of its 494 correct answers there. This completed matrix supports that
specific deployment comparison; it does not promote any model or authorize a
model upload. Preserve skill-level gains and losses when choosing the next
mixed-review lesson block.

[All training trajectories](MINICPM-UPDATE-CURVES-PROGRESS.md) ·
[Rank-16 details](RANK16-PRECISION-PROGRESS.md) ·
[CSV](results/minicpm-20261026/final-checkpoint-precision.csv) ·
[Plot source](results/minicpm-20261026/plot_final_checkpoint_precision.py)

The earlier three-rank snapshot remains in
[its original JSON](results/minicpm-20261026/final-rank-precision.json).
