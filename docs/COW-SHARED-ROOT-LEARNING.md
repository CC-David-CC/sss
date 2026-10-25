# Native MiniCPM learning through COW

## Current curve snapshot: 85 scored checkpoints

The new snapshot contains 70 full-weight and 15 attached-LoRA checkpoints. Each
point is backed by a complete 864-question development assessment. Exact-weight
aliases can share one qualified assessment; 85 counts checkpoint positions, not
85 distinct runs or independent repetitions. The data preserves those aliases.
The full-weight data was
captured at 2026-10-25T13:13:00Z. These are continuing fixed-update trajectories,
not five completed 68-update studies. Gaps are left visible; no missing point is
interpolated or treated as a pass.

| Arm | Latest completed update | Correct / 864 | Naturally finished / 864 | Original wrong answers gained | Original correct answers lost |
| --- | ---: | ---: | ---: | ---: | ---: |
| AdamW full | 18 | 429 | 863 | 378 | 8 |
| Standard Muon full | 21 | 412 | 862 | 371 | 18 |
| RMS / decay Muon full | 18 | 394 | 859 | 353 | 18 |
| Fast-to-refine Muon full | 13 | 378 | 854 | 335 | 16 |
| AdamW LoRA, rank 16 (attached) | 15 | 396 | 862 | 346 | 9 |

This table reports progress, not an equal-update ranking: its rows have different
update counts. The graph compares measured points at their actual update/practice
positions. LoRA retains its separate runtime identity, with the previously checked
base and trained-model execution bridges; this does not waive its failed merged
GGUF deployment gate. None of these development observations promotes a model.
The original has 59 correct and 415 naturally finished responses. Full and LoRA
practice use the same fixed ordered stream, with 27 presentations per update.

[Full-weight snapshot](../validation/minicpm-native-learning-20261024/shared-learning-block-ax.json)
and [attached-LoRA snapshot](../validation/minicpm-native-learning-20261024/direct-lora-learning-ax.json)
include learning, original-answer losses and evidence identities. LoRA update 7's
native cost comes from its original completed update receipt (81.72 allocated
seconds), not the later readonly owner's zero-new-training allocation. Native
update 7 was not repeated. Shared-server timings include other workloads and are
not a controlled optimizer efficiency ranking.

The nine tested skill families are still a limited development slice. The full
68-update curves, broader harness/skill acceptance, selected-model quantization
and final report/cleanup remain unfinished. Earlier snapshots below are retained
as historical observations.

The full-weight snapshot contains 45 completed A100 training assessments and the original-model
baseline, captured 2026-10-25T10:49:05Z. All use the same frozen 864 development
questions, exact checker, 512-token context, greedy decoding and 64-token output
limit. Each native update presents the next 27 examples from the fixed practice
stream. No evaluation answers enter that stream.

![Measured shared-root learning and forgetting](images/cow-shared-learning.svg)

The figure also overlays six independently completed attached-LoRA observations,
with separate runtime identity and controlled execution bridges. It shows
correct answers, natural stopping, previously wrong answers
gained, and original successes lost. Every plotted point is a complete assessment;
gaps are not interpolated. The loss panel is out of the original model's 59
successes, rather than all 864 questions.

Latest completed point in each regimen (these update counts differ):

| Regimen | Completed updates | Correct / 864 | Naturally finished / 864 | Newly correct vs original | Original successes lost |
| --- | ---: | ---: | ---: | ---: | ---: |
| Original | 0 | 59 | 415 | 0 | 0 |
| AdamW full | 11 | 388 | 860 | 342 | 13 |
| Standard Muon full | 14 | 374 | 855 | 329 | 14 |
| RMS/decay Muon full | 12 | 353 | 855 | 306 | 12 |
| Fast-to-refine Muon full | 8 | 303 | 853 | 255 | 11 |
| AdamW LoRA, attached | 6 | 298 | 853 | 243 | 4 |

At a common six updates, all five series have seen 162 practice presentations:

| Regimen at update 6 | Correct / 864 | Naturally finished / 864 | Newly correct | Original successes lost |
| --- | ---: | ---: | ---: | ---: |
| AdamW full | 349 | 855 | 302 | 12 |
| Standard Muon full | 270 | 846 | 218 | 7 |
| RMS/decay Muon full | 271 | 847 | 220 | 8 |
| Fast-to-refine Muon full | 274 | 851 | 223 | 8 |
| AdamW LoRA, attached | 298 | 853 | 243 | 4 |

These are observations under the predeclared settings, not an optimizer ranking
or a claim that any learning rate is optimal. A larger total does not erase the
original successes lost. The original model's 59 successes are a small reference
set; the separate per-skill and gate aggregates remain in the data.

Earlier checkpoints have been backfilled under this exact runtime without
replaying their native updates. Each full-weight arm now has every completed
update from one through its latest plotted point. Identical weight artifacts can reference one
assessment, with explicit aliases rather than being counted as independent
trials. The artifact preserves each observed point and every skill/gate change.

The controlled 68-update comparison keeps its declared practice stream fixed.
Changing lessons for only one arm midway would change the experiment. A later
adaptive block can use the observed failure families to generate new verified
practice and mixed review, without copying these development answers.

At six updates, full AdamW has 51 more correct answers than attached LoRA,
while losing eight more of the original successes. These are different observed
learning/forgetting tradeoffs under the declared recipes, not a general verdict
on full training versus LoRA.

The separately bound LoRA hat reaches 298/864 correct after six updates, with
243 answers gained and four original successes lost. Its runtime identity differs
explicitly; original-model and saved trained-model bridge controls matched all
864 sampled sequences, and the native binaries are byte-identical. The overlay
retains these distinct declarations rather than labelling every series as one
runtime. The original merge-equivalence failure remains unchanged. See [the
learning data, controls and repeatable report command](MINICPM-DIRECT-LORA-LEARNING.md).

## Execution and timing

S3 uses PCC's existing COW consumed request, the same underlying request used
by BW. The 28-token common rendered input is materialized once, and each
question branches from that root. Setup work is counted separately. These
direct-answer tests do not execute a BW tool workflow.

The new original-model baseline produced **identical sampled token sequences
and outcomes on all 864 questions** to the saved previous COW assessment:
59 correct and 415 naturally finished. Runtime identity changed explicitly to
bind the shared-prefix policy and the frozen implementation.

This baseline took **67.0 minutes** under its shared A100 load, versus **19.1
minutes** for the earlier COW run. Workload and timing conditions differed;
this is not evidence that saving 28 prefix tokens caused a slowdown, and it is
not a new speedup claim. The earlier [original/trained execution comparisons](COW-FIRST-DATA-BLOCK.md)
and their observed 6.1x / 2.7x ratios remain separate measurements.

Candidate assessments now proceed independently of the baseline's scheduling.
Learning/forgetting comparisons require its completed matching result. Native
updates remain ordered within each arm, with exact moments and example cursors
continued from their saved checkpoints. Models stay on their own hosts.

The runs are repeatedly observed development measurements. Sealed acceptance,
the complete 68-update curves, the matched-practice LoRA curve and broad
administration/tool/research qualification remain unfinished.

[Aggregate counts, skill/gate changes and evidence identities](../validation/minicpm-native-learning-20261024/shared-learning-block-aq.json).
The raw private responses and model files are not published.


## Placement on the shared server

A later owner audit found an AdamW update-10 assessment getting roughly 9-11%
process SM activity while another workload used 88-98%, with two suitable cards
idle. The placement preference put memory fragmentation ahead of utilization.
The corrected owner preference considers observed utilization first, retaining
the same memory admission and PCC GPU leases. All four A100 full-weight arms
were handed off independently after their native checkpoints were verified.

The old assessment completed **543 questions in 127.3 minutes**. Reassessing that
same saved model completed **all 864 in 9.3 minutes** on a less contended card.
Every overlapping sampled sequence and case outcome matched exactly. Original
partial evidence was retained, native update 10 was not repeated, and the
numerical runtime/checker/policy stayed fixed. This is an operational placement
observation across different shared loads and panel lengths. It does not isolate
an algorithm throughput gain. A nearly finished fast-to-refine assessment was
allowed to finish and its complete result reused with zero duplicate allocation.

[Placement observations and overlap control](../validation/minicpm-native-learning-20261024/evaluation-placement-ap.json)
keep the model/runtime identities, counts and timing limits alongside the data.


### Attached-LoRA placement control

The same problem later affected the directly attached hat at update 7. Its
original assessment completed 246 questions in 59.6 minutes on a heavily shared
card. After preserving the completed native update and moments, a new readonly
assessment completed all 864 in 12.3 minutes on another card. All 246 overlapping
sampled sequences and case outcomes matched exactly; this checkpoint scored
320 correct and 853 naturally finished responses. Native update 7 was not
repeated, and its original partial evidence remains available.

The new LoRA owner samples utilization three times and admits readonly
evaluation only when the peak observed utilization is at most 50%, alongside the
existing memory and lease checks. This is an admission observation; workloads
can change after launch. The four full-weight owners still use their earlier
utilization-first preference. This does not establish maximal fleet efficiency.
Different shared loads and unequal partial/full panels prevent treating these
wall times as a kernel or training-efficiency comparison.

[Same-hat overlap control and placement data](../validation/minicpm-native-learning-20261024/direct-placement-as.json)
are separate from the earlier six-point LoRA curve snapshot above.

## Saved-matrix geometry at equal practice

The [eight-update matrix report](OPTIMIZER-GEOMETRY.md) joins exact saved-weight
and accumulated-change spectra to these scored model identities. Weight rank,
change rank, answer gains and original-answer losses are separate measurements.

The [update-14 to update-15 parent comparison](NEXT-SKILL-BLOCK.md#later-exercise-net-gain-can-hide-substantial-churn)
also records 12 newly correct and 11 newly wrong answers behind a net gain of
one. Original-baseline retention and immediate-parent retention are different
measurements; both matter when choosing the next mixed-practice block.
