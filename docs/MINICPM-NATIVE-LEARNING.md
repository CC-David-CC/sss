# MiniCPM: learning and forgetting at matched practice exposure

The next comparison measures every update of AdamW, standard Muon, RMS/decay
Muon and fast-to-refine Muon, plus an AdamW LoRA control. Training time is a
measurement, not the organizing principle or a stopping budget. The old timed
experiment remains below as historical evidence; it is not an equal-exposure
comparison. Full-model training and held-out assessment are already real; the
new finer curves are running. The [current combined graph](COW-SHARED-ROOT-LEARNING.md)
shows measured learning and forgetting. The separately qualified
[attached-LoRA curve](MINICPM-DIRECT-LORA-LEARNING.md) reaches 231/864 correct
after three updates; the original merged-deployment gate remains failed.

## Initial per-update snapshot (earlier execution path)

[Saved initial partial chart](../validation/minicpm-native-learning-20261024/learning-curve-progress.png) ·
[CSV](../validation/minicpm-native-learning-20261024/learning-curve-progress.csv) ·
[Aggregate points](../validation/minicpm-native-learning-20261024/curve-points-progress.json).

The first measured point is **full AdamW update 1**: 27 practice presentations
produce 234/864 exact answers versus 59 at update 0. It gains 176 answers and
loses 1 original success. Natural completion improves 415 to 786. Standard Muon update 1 has now also completed: 109/864 correct, 587 finished,
51 answers gained and 1 original success lost after the same 27 presentations.
The other three arms remain at their shared baseline in this partial plot.
These are actual held-out outcomes, not a training-loss prediction. One update
does not establish the eventual ordering of these declared regimens.

All four full-update regimens restart from the same original MiniCPM weights.
Every update consumes the same ordered batch of 27 checked practice examples.
Measure every update 1 through 68 on the same full 864-case development set:
340 post-update evaluations across five arms, with no training-phase time cap.
Do not reset optimizer moments or the data cursor between curve points.
The native execution deadline remains a lifecycle guard, not a scientific budget.

The primary chart will show original answers gained, original answers lost,
net exact accuracy and natural completion against update count. Additional
views will show practice/supervised-token exposure, measured training work,
checkpoint/evaluation overhead and GPU memory. At 42 updates each arm has seen
1,134 presentations; at 68 it has seen 1,836. These are repeated ordered practice
presentations, not that many distinct new questions. The 68-update curve is a
descriptive experiment; subsequent hill-climbing is informed by its data.

The unchanged-original F32 behavior control is complete: 59/864 correct and
415/864 naturally finished, with every case outcome equal to the original-F16
reference. [Measured control](../validation/minicpm-native-learning-20261024/original-F32-control.json). This separates learned changes from saved-weight
precision/kernel differences. Full-weight checkpoints use F32. The original
merged-LoRA deployment remains gated. The separate attached-hat series keeps
the original F16 base and its immutable adapter, with actual runtime identities
and original/trained execution controls retained. The new F16 and F32 COW
baselines match every sampled token on all 864 cases.

The LoRA comparator uses native AdamW, rank 16/alpha 16, all 294 hidden linear
matrices plus the prediction head, and freezes embeddings and norm/gain weights.
Its initial 1e-4 learning rate is a declared starting regimen, not an optimality
claim. Tiny CPU and CUDA tests now establish exact uninterrupted-versus-resumed
adapter weights/moments. A native F32 merge and its real-model numerical check
still gate that arm. Full-update arms are tracked independently.

The four full-update settings remain the declared rates/scaling/decay shown in
the historical configuration table below. Different rates, decay and adaptation
capacity are part of the regimens. Equal exposure supports an honest comparison
of these regimens; it does not isolate every individual design choice. Repeated
development feedback is not sealed qualification or proof of broad competence.

[Predeclared curve protocol and exact settings](../validation/minicpm-native-learning-20261024/per-update-curve-protocol.json).
Curves and aggregate points will be published as actual results arrive. No
interpolated points or anticipated gains are measurements. Checkpoints remain
private on fleet storage; no model upload is authorized.

## Standing goal and continuous loop

Improve S3, BW and PCC into a reusable system that observes a failure, creates a
verified lesson, trains a candidate, measures learning and forgetting, and accepts
or rejects a change, with evidence and documentation another person or model can
repeat. Run this as continuing work:

**test → choose lessons → train → test → report → preserve a named GGUF → repeat**

The owner explicitly prefers carrying a substantially improved checkpoint forward
when a smaller number of skills regress. Those regression families become practice
in the next mixed skill block alongside retained skills and forward learning. A
failed strict-preservation check is recorded faithfully; it does not discard the
working checkpoint or force a restart from the original weights. Evaluation
answers remain protected: teach new checked variations of failure types.

Preserve named standalone F32 GGUF variants, scores, training lineage, reasons to
try them and limitations for later local experiments. The model files remain
unpublished. Code and aggregate results continue through the authorized Git route.
This loop is standing work within existing owner resource permissions, including
the A100 campaign ceiling; it continues until the owner stops or redirects it.

The [cross-project implementation design](https://github.com/CC-David-CC/Private_Context_COW/blob/feat/native-training-budget-20261024/docs/NATIVE-LEARNING-LOOP.md)
places durable execution in PCC, curriculum/scoring in S3 and driving tools in BW.
The [implemented native job commands](https://github.com/CC-David-CC/Private_Context_COW/blob/feat/native-learning-path-20261024/docs/NATIVE-LEARNING-JOBS.md)
now expose registered AdamW/Muon profiles and private named GGUF preservation.
Tiny native CPU HTTP/CLI mechanics pass; full-model GPU pathway exercise is in
progress. Durable automatic multi-round orchestration and the BW driver remain unfinished.

## Historical baseline

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

## Historical timed candidate: large gains, retention rejection

The unchanged-harness AdamW control improves exact answers from **59/864 to
482/864** (6.83% to 55.79%). Natural completion improves **415/864 to 864/864**.
There are 434 gained answers and 11 lost previous successes; 48 earlier passes
are retained. Completion gains are 449 with no losses. The frozen strict gate reports a preservation failure. The owner has retained
this substantially improved model as a working checkpoint for mixed repair and
continued learning. No sealed qualification was run and no model was promoted.

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
original cases are used before/after. The harness was held fixed. Original saved weights were F16 and the trained
weights are F32. The subsequently completed unchanged-original F32 control
reproduces all 864 original pass/completion outcomes, so the measured gain is
not explained merely by that saved-weight conversion. This does not isolate learned arithmetic from
better formatting/stopping. The unchanged correctness path now needs 6,884
model calls and 1,017,029 prefill tokens instead of 35,132/4,523,170; shorter
responses reduce this fresh-prefix oracle's repeated work. No production serving
speedup is claimed. [Full aggregate and paired skill/gate results](../validation/minicpm-native-learning-20261024/adamw-control.json).

## Historical time-limited program and implementation

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
149 standard-library core tests and three optional token-protocol tests pass.

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


## Continuous repair implementation checkpoint

The owner has explicitly retained the improved model and requested the cycle to
continue. `sss.learning.next_skill_block` now distinguishes a useful working
checkpoint from the historical strict-preservation result. It records original
baseline and immediate-parent comparisons, keeps cumulative losses visible, and
proposes repair/review/forward-learning groups without exporting test answers.

The next checked block selects 960 admitted practice occurrences from an expanded
1,728-example pool using the same generation seed. Each 30-example update has 27
review slots (nine skills times three gates) plus one extra lesson for fraction
transfer/recovery, fraction composition and independent place value. The extra
lessons have distinct admitted identities. Original protected questions remain
identical. No public-source rows enter this block. New curriculum means explicitly
fresh optimizer moments while keeping the improved parent weights; exact same-data
optimizer resume remains a separate operation. 149 core tests pass at this point.

The offline integration command now accepts an explicit working-parent result and
its source practice document for that transition. A new-data gradient check and
actual mixed-repair training/evaluation have completed after the frozen four-arm
comparison. The offline new-data transition is GPU-qualified by that run. The
new registered native HTTP/CLI pathway is separately CPU-qualified and is now
being exercised on the full model. Automatic durable multi-round control and
the BW driver remain unfinished.

[Quantization-retention experiment](https://github.com/CC-David-CC/Private_Context_COW/blob/feat/native-training-budget-20261024/docs/MINICPM-QUANTIZATION-STUDY.md)
compares original and trained models in F32, F16, Q8, Q5, Q4, Q3, Q2 and Q1_0.
Eight full assessments are complete. The trained variants score FP32 482/864,
FP16 481, Q8 482 and Q4 467; all finish every response. Original same-format
scores are 59, 59, 41 and 37. Q8's unchanged total includes two gains and two
losses versus trained FP32; Q4 gains 19 and loses 34. Its 1.56 GB artifact keeps
most of the measured improvement. Q5/Q3/Q2/Q1 tests are still running. [Precision results and repeatable report command](MINICPM-QUANTIZATION-RESULTS.md).
The 6.8% original score is not assumed to be an upper bound for other formats.
Model files stay local and unpublished; code and aggregate evidence remain public.


## Standard Muon control

Standard Muon reaches **473/864 exact answers and 864/864 completions**, with 437
gains and 23 lost original successes. It completes 43 updates/1,161 practice
presentations in 305.77 training-phase seconds, compared with AdamW's
68/1,836 in 303.23 seconds. Both are retained as local experimental standalone
F32 variants. The current AdamW checkpoint remains the planned mixed-repair parent.
Native grouping uses Muon for 294 matrices and auxiliary AdamW for 87 tensors.
[Measured timing, groups and paired losses](../validation/minicpm-native-learning-20261024/muon-standard.json).
Different main learning rates and data exposure remain part of these declared
regimens; the 9-answer total difference is not a controlled optimizer-only causal
claim or a general ranking. Completed RMS/decay and refinement measurements
appear below.

The prepared repair block has 944 distinct questions and 16 explicitly counted
rehearsals across its 960 occurrences. [Finished checked practice](../examples/finished-training-examples/minicpm-mixed-repair/practice.txt)
and its diversity manifest contain no protected test answers.

## Historical time-limited comparison and second learning checkpoint

The four declared regimens have all completed the same frozen 864-case
development assessment. These are one-run measurements on the dedicated
Blackwell, not shared A100 timing samples.

| Regimen | Exact answers /864 | Natural completions /864 | Full updates | Practice presentations | Training-phase seconds | Original answers gained/lost |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| AdamW |482|864|68|1836|303.23|434 / 11|
| Standard Muon |473|864|43|1161|305.77|437 / 23|
| RMS/decay Muon |464|864|42|1134|300.09|428 / 23|
| Fast-to-refine Muon |465|864|34|918|307.85|425 / 19|

Fast-to-refine actually exercised its refinement schedule. Each variant remains
preserved as a named standalone local F32 GGUF, with lineage and limitations.
The historical strict gate rejected all four for lost previous answers. Those
records are retained alongside the owner's working-checkpoint policy.

In this implementation standard Muon's optimizer phase took about 2.72 seconds
per update versus AdamW's 0.061 seconds; matrix projection cost outweighed the
cheaper state representation. The time cap therefore exposed Muon to fewer
practice presentations. This is actionable native implementation evidence, not
a claim that Muon generally trains worse or that equal update counts would
produce the same ranking. Main rates, scaling, decay and exposure differ between
regimens. Effective-rank and update-geometry measurements remain pending.

**MixedRepair-02 then improves AdamW's 482/864 to 507/864 (58.68%).** It gains
51 answers and loses 26 relative to its immediate parent: net +25. Relative to
the original it gains 458 and loses 10: net +448. Natural completion changes
864 to 860; all four new unfinished responses occur in fraction-add composition.
Several other composition/state groups remain weak. Report the lost cases as
well as the higher total, and teach checked variations in their families.

This block performs 62 full updates /1,860 presentations in 302.31 training-phase
seconds on the 960-occurrence mixed curriculum described above. Every update
again has 381 finite/nonzero gradient tensors; saved-model reload mean-loss error
is 2.83e-9. Both parent and child store F32 weights and use the same runtime,
checker, cases and limits, providing a cleaner learning comparison than the
original-F16 versus first-trained-F32 contrast. No public dataset rows were used.

The owner retains this improved checkpoint and carries its failures into the
next block. The next checked selection has 1,344 lessons in 32 batches of 42:
27 review slots cover every existing skill/gate and 15 additional slots target
regression families. This is increased mixed repair, not training on protected
answers. Its actual native HTTP/CLI run is in progress; no third score is claimed.

[Complete aggregate measurements, all skill/gate groups, timing and repair proposal](../validation/minicpm-native-learning-20261024/comparison-and-repair.json).
These development measurements guide repeated improvement; they do not establish
sealed qualification, Linux/tool-use improvement, broad retention or production
serving throughput. No model file has been uploaded.

## Reproduce the curve charts from aggregate evidence

S3 now validates each measured curve point: the original-answer gains/losses
must reconcile its net score, update counts must match practice exposure, and
all points must bind the declared protocol. Missing checkpoints are not
interpolated, and a complete claim requires every declared point in every arm.
The validator is standard-library code; plotting is an optional dependency.

From the S3 checkout, with an isolated Python environment:

```sh
python -m pip install '.[plots]'
python -m sss.plot_curves \
  --protocol validation/minicpm-native-learning-20261024/per-update-curve-protocol.json \
  --input curve-points.json --output-prefix report/learning-curve
```

This exports PNG, SVG, CSV and a JSON provenance/coverage record. Each figure
labels the last measured checkpoint per arm; a partial curve remains partial.
Four validator tests pass, including a flat net score that hides lost original
answers, missing points, changed exposure and false completion. The optional
renderer also runs on a clearly labeled synthetic validation fixture; that
fixture is not a model finding. The base S3 package remains importable without
Matplotlib, BW, PCC, a GPU or a network connection.

[Native AdamW LoRA and F32-merge mechanics](https://github.com/CC-David-CC/Private_Context_COW/blob/feat/native-learning-curves-20261024/docs/NATIVE-PER-UPDATE-CURVES.md)
now pass the declared small numerical gates. Actual-model merge parity remains
a separate first-point gate in that original snapshot. The later
[attached-hat study](MINICPM-DIRECT-LORA-LEARNING.md) now has measured learning
scores, without waiving the failed merged-deployment gate.

## Completed HTTP/CLI block: a tie with worse completion

MixedRepair-03 has completed through the real PCC HTTP/CLI path. It retains
**507/864 correct answers**, while natural completion falls 860 to 853. S3 keeps
the preceding 507/860 working parent. The checkpoint is preserved privately as
a named standalone F32 GGUF, with this result attached. This is useful machinery
evidence, without a further learning gain.

All 1,344 selected lessons were actually consumed: 46 full updates/1,932 practice
presentations, 381 finite/nonzero gradient tensors each update, and saved-model
reload mean-loss error 8.19e-10. The run's 301.77 training-phase seconds are part
of the historical timed experiment that was already complete when the owner
removed time as the organizing principle. Subsequent curve requests omit that
training-phase cutoff entirely. [Aggregate results and next-block decision](../validation/minicpm-native-learning-20261024/native-api-repair03.json).

## Checkpoint retention during and after this report

The owner selected milestone models and optimizer states, about 1 TB for this
study. Keep updates 1, 2, 4, 8, 16, 32, 42, 64, 68, plus each arm's live parent and best
checkpoint so far while the study runs. All scores and response evidence remain.
S3 selects retained checkpoint identities; PCC validates the owned archived
artifacts and retires superseded model/state files only after a verified later
checkpoint exists. Named hardlinks are retired with their expired binaries.

After the completed report is identified and published, delete superseded
study binaries, including milestone optimizer states. Retain the original base,
selected current model and all source, scores, traces and plots. This cleanup
does not run while the report is unfinished. The original archive verification
records and separate retirement receipts preserve what was verified and why
an artifact later expired. Changed files or uncertain ownership stop retirement.


See [shared evaluation execution](COW-EVALUATION.md) for the optional common COW request path and its numerical checks.
