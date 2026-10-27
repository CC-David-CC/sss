# Final-checkpoint precision: AdamW, standard Muon and six LoRA ranks

Snapshot: 2026-10-27T02:14:03.730319+00:00. **All eight finished training arms have
completed all eight formats: 64 model/format panels, each with 864 questions.**
Every arm shown here completed 68 updates and 1,836 ordered practice
presentations. The RMS/decay and fast/refine Muon variants are still completing
training; their final precision sweeps are not included yet. Endpoints are
fixed at update 68, not selected by each arm's peak development score.

![Final-checkpoint precision comparison](results/minicpm-20261026/final-checkpoint-precision.png)

The original model appears at every format, with its F16 reference also shown
as a horizontal line: **59 correct, 415 naturally finished**. Its existing F32
run was independently audited and included without new inference. The original
sweep used a prior runtime, so this is a historical reference rather than a
matched-runtime causal estimate of training alone. Within each trained arm,
quantized outcomes are paired against that arm's own F32 reference.

## Correct answers out of 864

| Format | Original | Full AdamW | Standard Muon | LoRA r1 | LoRA r2 | LoRA r3 | LoRA r4 | LoRA r8 | LoRA r16 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| F32 | 59 | 482 | 494 | 450 | 479 | 475 | 493 | 492 | 494 |
| F16 | 59 | 481 | 494 | 450 | 479 | 475 | 493 | 492 | 494 |
| Q8_0 | 43 | 480 | 498 | 446 | 480 | 474 | 493 | 488 | 491 |
| Q5_K_M | 58 | 468 | 491 | 438 | 466 | 469 | 484 | 487 | 482 |
| Q4_K_M | 34 | 471 | 471 | 409 | 460 | 457 | 486 | 479 | 492 |
| Q3_K_M | 50 | 346 | 353 | 268 | 260 | 297 | 364 | 315 | 401 |
| Q2_K | 4 | 35 | 28 | 21 | 16 | 23 | 14 | 31 | 36 |
| Q1_0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

## Naturally finished responses out of 864

| Format | Original | Full AdamW | Standard Muon | LoRA r1 | LoRA r2 | LoRA r3 | LoRA r4 | LoRA r8 | LoRA r16 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| F32 | 415 | 864 | 864 | 863 | 864 | 864 | 864 | 864 | 864 |
| F16 | 415 | 864 | 864 | 863 | 864 | 864 | 864 | 864 | 864 |
| Q8_0 | 392 | 864 | 864 | 863 | 864 | 864 | 864 | 864 | 864 |
| Q5_K_M | 398 | 864 | 864 | 863 | 863 | 864 | 864 | 864 | 864 |
| Q4_K_M | 522 | 864 | 864 | 811 | 862 | 864 | 864 | 864 | 864 |
| Q3_K_M | 475 | 863 | 864 | 797 | 795 | 840 | 831 | 863 | 863 |
| Q2_K | 521 | 821 | 830 | 825 | 811 | 815 | 778 | 824 | 817 |
| Q1_0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

Every zero is a measured result. These 64 panels represent 55,296 question
attempts in the finished endpoint comparison, including previously completed
F32 references reused under their exact runtime/input checks. This report
itself started no model call or training update.

## ELI5

Eight students finished the same 68 practice sessions. We then packed each
one into eight file sizes and asked every version the same 864 questions.
We now have all those answers for these eight students. Two other students
are still finishing their practice, so their final packing tests come later.

Smaller files usually preserve much of the measured improvement down to Q4,
then drop sharply at Q3 or below. It is not a perfectly smooth curve: the
standard Muon endpoint scored 494 at F32 and 498 at Q8. That is a result on
this test, not proof that shrinking a model generally makes it smarter.

## Master's level

All formats originate directly from each arm's own F32 master. LoRA masters
were produced by PCC's native merge and independently checked against FP64
weight reconstruction before conversion. Full AdamW and standard Muon already
produce full F32 models; their existing complete F32 assessments were reused
after exact runtime/input verification. Attached-adapter assessments were not
silently treated as standalone-merge assessments.

The evaluator uses the shared-prefix PCC/COW path with greedy decoding,
512-token context and 64-token output bounds. Exact model hashes, runtime and
checker identities, settlement hashes and per-skill/gate transitions are retained.
F16 had identical answer and finish verdicts to F32 in 7 of these
eight arms; this does not claim identical logits or response text.

Totals hide turnover. Full AdamW's F16 score of 481 combines one gained and
two lost answers relative to F32. Rank 16's Q4 score of 492 combines 20 gained
and 22 lost answers. Standard Muon's Q8 result combines 6
gained and 2 lost answers, for a net increase of four.

## PhD level and limits

The comparison controls update count and ordered practice exposure, not wall
time. Hardware/runtime distinctions remain explicit. These are development
questions under an output bound, without independent-seed repetitions or sealed
broad-task acceptance. The missing two final arms prevent a complete optimizer
comparison. The shown update-68 endpoints are not necessarily the best earlier
checkpoint or best candidate for every skill or quantization size.

Quantization can change a correct answer in either direction; a nearby total
does not establish behavioral equivalence. These are post-training conversions.
Quantization-aware training was not used and remains a follow-up for Q4 and below.

## Recovering two slow evaluations without repeating completed cases

Rank-2 Q2 and standard-Muon Q3 were running on heavily contended GPUs 0 and 2.
Other processes were observed using about 98% of those cards' compute. The owner
requested relocation. The original workers were interrupted only after checking
destination leases, memory, source, model and runtime bindings.

The continuation preserved **328 rank-2 Q2 cases** and **257 standard-Muon Q3
cases**, then evaluated only the respective 536 and 607 missing inputs on GPUs
7 and 1. Existing token receipts were decoded and independently regraded;
original hashes were checked again after completion. The reduction requires
disjoint coverage of all 864 original case identities and the same numerical
runtime identity. No completed case or training update was repeated. An
unfinished case may have had partial computation discarded during interruption.

The interrupted controllers' original failure records remain intact. Their
separate validated continuation records identify the completed result; the
[aggregate evidence](results/minicpm-20261026/final-checkpoint-precision.json)
includes each recovery's source-map and pointer hashes. This is not a silent
conversion of an interrupted run into a successful original execution.

Recent per-case timing fell from about 13 seconds on the busy cards to roughly
0.65–0.73 seconds after relocation. These are observations under changing shared
load, not an isolated quant-kernel benchmark or a universal 20× speed claim.

## Applied meaning

Choose a quantized model from measured skill results, memory and deployment
needs. Rank 1, for example, falls from 450 to 409 correct at Q4 and loses
52 natural finishes, whereas rank 16 keeps 492/494 correct and all finishes at
Q4. Broader tests and the two outstanding variants remain necessary. No model
is promoted or uploaded by this report.

[Training trajectories](MINICPM-UPDATE-CURVES-PROGRESS.md) ·
[Rank-16 details](RANK16-PRECISION-PROGRESS.md) ·
[CSV](results/minicpm-20261026/final-checkpoint-precision.csv) ·
[Plot source](results/minicpm-20261026/plot_final_checkpoint_precision.py)

The earlier three-rank snapshot remains in
[its original JSON](results/minicpm-20261026/final-rank-precision.json).
