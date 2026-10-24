# Preparing the MiniCPM fixed-compute comparison

The native training machinery is qualified on the dedicated RTX PRO 6000 and
now on an A100. The larger S³ practice/evaluation set passes actual MiniCPM
rendering, tokenization and PCC lesson admission. This checkpoint does not
contain a learning winner, acceptance decision or a training run on this set.

## Data foundations

The first attempt to expand the legacy generator to 96 checks per leaf found
seven repeated protected questions. Two crossed development/qualification; the
other five repeated within development. The guard refused that pack before any
model run. Its original collision evidence is retained by hash/coordinates.

The new explicit `without-replacement-v1` profile fixes the two colliding finite
families: multiplication uses an injective permutation of operand-pair ordinals;
place value uses unique factor/position ordinals and disjoint split magnitudes.
It does not redraw questions until a set passes or pad duplicates with new IDs.
Other family generators retain their original behavior. Every protected question
still passes the cross-split duplicate check. An exhausted family fails admission.
Legacy profile questions, count limits and the published three-example pilot's
pack identity remain unchanged; the compatibility test checks that exact identity.
The new profile also binds its generator source hash into the pack identity.

The prepared study covers nine existing prerequisite-connected leaves: place
value; addition without carry and with carry; signed addition; multiplication;
division; fraction equivalence and addition; and register state tracking.
Each leaf has independent, composition and transfer/recovery gates.

| Split | Per leaf | All nine leaves | Status |
| --- | ---: | ---: | --- |
| Practice | 96 occurrences | 864 occurrences | 850 distinct questions, 14 recorded rehearsals |
| Development | 96 checks | 864 checks | All unique, separate from practice/qualification |
| Qualification | 96 checks | 864 checks | All unique, separate from practice/development |

Each split uses 32 cases per gate. These counts describe this arithmetic/state
curriculum. They do not establish code, Linux, tool-use, long-context or research
mastery. A 96-question percentage still needs its denominator, paired changes
and uncertainty. The pack remains explicitly outside formal mastery qualification.

All checked practice passes the real PCC schema-2 lesson boundary using the
qualified MiniCPM renderer/tokenizer. The longest training input is 379 tokens;
the largest selected answer is 26 tokens. The largest evaluation prefix is 354
tokens. Training fits the qualified 512-position/256-target path. Evaluation must
provide sufficient context for prefix plus generation: the legacy oracle's
256-token default is too small; use a separately qualified 512-token context.
No question was truncated or silently dropped. Thinking is off and answer targets
are independently checked; this pack supplies no attested thinking spans.

[Aggregate preparation evidence and original collision coordinates](../validation/learning-program-20261024/fixed-budget-preparation.json).
[Finished practice TXT and manifest](../examples/finished-training-examples/minicpm-fixed-budget/practice.txt).
Protected questions and answers remain private and are excluded from the TXT and
training-worker export. The training file contains practice only.

## Reproduce preparation

From this S³ source branch and matching PCC sources, with the qualified local
F16 MiniCPM model and Python environment:

```sh
python -m unittest discover -s sss_tests
python -m sss_integration.optimizer_study_prepare \
  --pcc-root /source/pcc --model /models/MiniCPM5-2B-F16.gguf \
  --model-contract-id EXACT_QUALIFIED_MODEL_CONTRACT_ID \
  --output /private/new-study-data \
  --skills math.add.carry math.fraction.add state.registers \
  --seed 20261024 --practice-per-gate 32 --checks-per-gate 32 \
  --generation-profile without-replacement-v1
```

Prerequisite closure supplies the other leaves. The seed controls example
generation; it is not a different-seed model-repeat campaign. The command has
no training runner. It checks every lesson before admitting any, writes the
finished practice TXT, and exports practice, development and qualification into
separate private files with identities. Preserve the exact source and inputs.
125 core tests pass, including collision prevention, checker agreement, source
binding, legacy identity and finite-family exhaustion.

## A100 qualification

On one shared A100-SXM4-80GB, six independent tiny optimizer-math cases pass,
covering 4,264 scalar comparisons with worst absolute error 8.40e-8. All four
tiny full-backprop arms pass completed save/resume and 14 state/error refusal
checks. Real MiniCPM backprop covers all 381 parameter tensors with finite,
nonzero gradients on the earlier 120-token pilot example, without updating or
exporting real-model weights. This is gradient coverage, not an independent
value-by-value check of all real-model derivatives.

The same qualified native trainer/header sources were built against a separately
fingerprinted A100 F32 CUDA backend with fast math removed. No PyTorch is used.
The owner permits admission based on free VRAM despite shared compute activity;
contention is retained in the record. The GPU work used about 0.00967 A100
allocation-hours; CPU compilation is separate. These timings are not a clean
Blackwell/A100 performance comparison. [Full qualification evidence](../validation/learning-program-20261024/a100-optimizer-qualification.json).

## Next execution gates

Freeze optimizer settings, mixed-review weights, model/harness/evaluator versions
and per-arm training budgets before observing development behavior. The current
native alarm is a job deadline, not a completed-update training-budget scheduler;
record and implement the latter before claiming fixed-compute learning results.
Its granularity must be stated in whole updates, with actual time and any budget
remainder/overrun exposed. Do not equate a fixed number of steps with equal cost.

Qualify actual-model gradients for this set's longer maximum input, and the
512-token evaluation context. Measure a baseline before training. Keep standard
Muon, RMS/decoupled-decay Muon, the defined fast-to-refine schedule and AdamW
control distinct. Report rank/geometry diagnostics separately from capability
scores. Broad AdamW ablations remain stretch work. Preserve per-question and
per-domain retention gates and the sealed final assessment.

BW's shell verification/termination issue remains separate; this preparation is
not evidence that training repaired it. The previous pilot's exact state
continuation is described in [the real-model mechanics report](MINICPM-OPTIMIZER-PILOT.md).
