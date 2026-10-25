# Learning through the shared-root COW evaluator

The new A100 runtime has a complete original-model baseline and six completed
training assessments in this snapshot. All use the same frozen 864 development
questions, exact checker, 512-token context, greedy decoding and 64-token output
limit. Each native update presents the next 27 examples from the fixed practice
stream. No evaluation answers enter that stream.

![Completed shared-root learning observations](images/cow-shared-learning.svg)

| Regimen | Completed updates | Correct / 864 | Naturally finished / 864 | Newly correct vs original | Original successes lost |
| --- | ---: | ---: | ---: | ---: | ---: |
| Original | 0 | 59 | 415 | 0 | 0 |
| AdamW full | 5 | 327 | 854 | 277 | 9 |
| AdamW full | 6 | 349 | 855 | 302 | 12 |
| Standard Muon full | 3 | 216 | 698 | 160 | 3 |
| Standard Muon full | 4 | 247 | 804 | 191 | 3 |
| RMS/decay Muon full | 3 | 219 | 700 | 163 | 3 |
| Fast-to-refine Muon full | 3 | 219 | 700 | 163 | 3 |

AdamW update 6 gains 302 previously wrong answers and loses 12 original
successes: a net gain of 290 over the original's 59. The losses remain visible
by skill and gate in the aggregate evidence. A larger total is useful progress,
but it does not erase forgetting or establish broad model quality.

This is an incomplete learning curve, not an optimizer ranking. The rates and
regimens differ, and these rows have different update counts. The earlier
checkpoints still need assessments under this exact runtime; an independent
backfill job is doing that without replaying their native updates. Identical
weight artifacts can reference one assessment, with explicit aliases rather
than being represented as independent trials.

The controlled 68-update comparison keeps its declared practice stream fixed.
Changing lessons for only one arm midway would change the experiment. A later
adaptive block can use the observed failure families to generate new verified
practice and mixed review, without copying these development answers.

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

[Aggregate counts, skill/gate changes and evidence identities](../validation/minicpm-native-learning-20261024/shared-learning-block-z.json).
The raw private responses and model files are not published.
