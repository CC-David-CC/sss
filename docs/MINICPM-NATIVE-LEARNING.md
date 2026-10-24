# MiniCPM: measuring answers, instructions and stopping before training

A model can calculate an answer and still fail the task: it may add an unwanted
explanation, ignore JSON requirements or keep generating instead of finishing.
The first larger MiniCPM baseline now measures exact answers and natural response
completion separately. The first full-update candidate has completed its
learning/retention assessment: it gains strongly but fails preservation. Standard
Muon and its two declared variants are still in progress.

## What the baseline establishes

MiniCPM5-2B F16 completed all 864 development cases on one dedicated 96 GB RTX PRO
6000 Blackwell. **59/864 passed the existing exact-answer checker; 415/864 sampled
an assistant ending token before the 64-token cap.** The latter is completion,
not correctness. These are strict direct-answer stack results, not evidence that
the model cannot perform elementary arithmetic in another prompt/harness.

The pack covers nine math/state leaves, 96 cases per leaf, split across independent,
composition and transfer/recovery gates. Practice, development and sealed
qualification are separate; protected answers never enter a lesson. The existing
checker was neither relaxed nor replaced with answer extraction after seeing the
responses. Generation is greedy, thinking is closed in the qualified MiniCPM
chat template, and the context/batch limits are both 512 tokens. No input is
truncated. The sampled stop IDs are 1 and 130073.

The separately qualified native oracle recomputes the complete prefix for each
output token and requests all position logits before returning the last vector.
This deliberately matches the qualified execution shape. It is a correctness
path, not a production KV-cached serving benchmark: 35,132 model calls processed
4,523,170 prefill tokens, with 2,776.12 allocated GPU seconds. Do not use this time
to estimate production inference throughput or shared A100 costs.

[Baseline totals, all 27 skill/gate groups and identities](../validation/minicpm-native-learning-20261024/baseline.json).
Raw protected prompts, answers and response traces stay private.

## First measured candidate: large gains, retention rejection

The unchanged-harness AdamW control improves exact answers from **59/864 to
482/864** (6.83% to 55.79%). Natural completion improves **415/864 to 864/864**.
There are 434 gained answers and 11 lost previous successes; 48 earlier passes
are retained. Completion gains are 449 with no losses. The frozen gate rejects
this candidate. No sealed qualification was run and no model was promoted.

Nine answer losses are fraction transfer/recovery, one is fraction composition,
and one is independent place value. Do not teach those protected questions back
to the model. Build independently checked practice variations in those families
and preserve mixed review before testing a repair. Several composition/state
families remain at zero exact passes; stopping correctly is not semantic mastery.

Training completes 68 full updates and 1,836 practice-example presentations in
303.23 training-phase seconds, including 3.23 seconds of final-update overrun.
The 864-occurrence ordered practice set is traversed 2.125 times, not 1,836 unique
questions. All updates cover all 381 finite/nonzero model gradient tensors; the
candidate reload mean-loss error is 3.41e-9. Gradient/coverage takes 211.99 seconds,
optimizer work 4.12 seconds, and post-update batch loss checks 87.10 seconds.
The operator's full GPU allocation is 459.06 seconds including preparation,
serialization, verification and reload. These are distinct clocks.

The same evaluation ID, runtime ID, checker, source oracle, generation policy and
original cases are used before/after. Thus this measured stack change follows
training, not a simultaneous harness change. It does not isolate learned arithmetic
from better formatting/stopping. The unchanged correctness path now needs 6,884
model calls and 1,017,029 prefill tokens instead of 35,132/4,523,170; shorter
responses reduce this fresh-prefix oracle's repeated work. No production serving
speedup is claimed. [Full aggregate and paired skill/gate results](../validation/minicpm-native-learning-20261024/adamw-control.json).

## From preparation to the first learning comparison

The 379-token longest practice example passes full ordinary backpropagation:
all 381 model parameter tensors have finite, nonzero gradients. This is gradient
coverage, not an independent scalar check of every real-model derivative. An
earlier three-example pilot already performed real full updates, validated reload
and exact completed-state continuation. Neither fact establishes held-out learning.

The new PCC trainer adds an opt-in training-phase budget. It finishes an entire
update before stopping and records the final-update overrun. Loading, checkpoint
serialization, diagnostic reload and evaluation are outside that training-phase
clock; their wall/allocation costs are recorded separately. A hard native job
deadline still applies. The helper refuses an older executable that would silently
ignore the budget. CPU and CUDA tests each pass AdamW/Muon continuation, exact
uninterrupted-versus-resumed tiny weights/moments, partial final batches, step-cap
behavior, default receipt compatibility and 19 refusal cases.

The [program frozen before baseline observation](../validation/minicpm-native-learning-20261024/learning-program.json)
orders 864 admitted practice occurrences into batches of 27: every update includes
all nine skills and all three mastery gates. There are 850 distinct practice
questions plus 14 explicitly recorded rehearsals. Training is ordinary full-weight
native backpropagation; no PyTorch or LoRA is used in these four arms.

| Arm | Main learning rate | Auxiliary AdamW rate | Matrix update |
| --- | ---: | ---: | --- |
| AdamW control | 0.000001 | same optimizer | elementwise AdamW, decay 0 |
| Standard Muon | 0.00005 | 0.000001 | original scaling, decay 0 |
| RMS/decay Muon | 0.000005 | 0.000001 | RMS scaling, decoupled matrix/auxiliary decay 0.1 |
| Fast-to-refine Muon | 0.000005 | 0.000001 | RMS/decay plus declared refinement from global update 4 |

Each arm starts from the same immutable base, has 300 training-phase seconds and
a 1,000-update cap, and uses the same ordered examples. Actual completed updates,
example/token work, optimizer/gradient/evaluation timing and overrun must accompany
the score. Equal time does not imply equal steps or equal examples. If update 4 is
never reached, the refinement arm has not exercised refinement. RMS plus decay is
a combined regimen, not an ablation isolating their individual effects. Broad
AdamW ablations and different-seed model-repeat campaigns are not this experiment.

The active source runner is `sss_integration.native_optimizer_step`. Its optional
`--program` and `--arm-id` bind a study arm; explicit CLI optimizer, settings,
rate, batch and cap must agree with that program. A practice document retains its
own `practice_id`; it is never relabeled as the earlier pilot. PCC owns the native
update, GPU lease, immutable candidate and optimizer state. S3 validates the
curriculum and grades frozen behavior. BW does not own these tests.

After each update run the candidate must reload and match the retained final
batch loss. Evaluate its exported weights with `sss_integration.optimizer_evaluate`
using exactly the baseline cases, checker, tokenizer, oracle build and generation
policy. `sss.paired.compare_frozen_evaluations` rejects missing/inconsistent
results, changed cases/runtime, any lost previous answer pass or completed response,
and candidates without a gain. A higher total cannot conceal a lost prior success.
Development eligibility still requires sealed qualification; it never promotes a
model. This nine-leaf study cannot establish Linux, coding, tool-use, research or
long-context retention.

[CPU budget evidence](../validation/minicpm-native-learning-20261024/cpu-budget.json),
[CUDA budget evidence](../validation/minicpm-native-learning-20261024/cuda-budget.json),
[source/gradient checks](../validation/minicpm-native-learning-20261024/source-checks.json).
140 standard-library core tests and three optional token-protocol tests pass.

## Next data round: corrected lessons, checked variation, public breadth

The owner approved public training sources/subsets. Finish the current frozen
comparison before changing its data. Then classify owned practice failures into
content, instruction, formatting, stopping and harness causes. Write a few
independently checked demonstrations for recurring model failures; synthesize
controlled variations and interleave retention review. Include the real assistant
ending token in the supervised target. Balance terse-answer tasks with requests
that legitimately need longer explanations. Synthetic reasoning is not assumed
correct merely because another model wrote it.

Candidate sources are [SmolTalk](https://huggingface.co/datasets/HuggingFaceTB/smoltalk)
constraint/rewrite/summarization subsets, [Tulu instruction following](https://huggingface.co/datasets/allenai/tulu-3-sft-personas-instruction-following),
and [Ai2 multi-constraint prompts](https://huggingface.co/datasets/allenai/IF_multi_constraints_upto5).
The last contains verifier metadata rather than supervised answer text; generate
and check any teaching response. Keep [IFEval](https://huggingface.co/datasets/google/IFEval)
and [IFBench test](https://huggingface.co/datasets/allenai/IFBench_test) as external
evaluation reserves, despite their Hub split names. Filter overlap and separate
problem/template families before training. Retain source revision, row identity,
license/attribution, transformations, verifier result and rejected samples. The
SmolTalk card licenses its newly generated subsets under Apache 2.0; incorporated
third-party subsets have their own licenses. The cited Ai2 training cards identify
ODC-BY. After owner approval, the pinned SmolTalk smol-constraints **train** shard and
card were staged: 16,862,908 parquet bytes plus 9,723 card bytes, revision
`5feaf2fd3ffca7c237fc38d1861bc30365d48ffa`. [Checksummed staging record](../validation/minicpm-native-learning-20261024/public-data-staging.json).
No rows have been admitted to training and the frozen optimizer comparison is
unchanged. Staging is not label verification or decontamination.

This remains work on the reusable learning loop. BW's shell verification and
termination failures are tracked separately; these scores do not demonstrate a
repair to those failures. Model/harness/data changes require separately reported
measurements so their effects remain distinguishable.
