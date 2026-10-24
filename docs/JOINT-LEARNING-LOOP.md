# Interleaving learning and harness improvement

The objective is a reusable loop that observes a failure, verifies a correction,
builds varied lessons, trains a candidate, measures learning and forgetting,
and makes an evidence-based keep/repair/reject decision. MiniCPM5-2B is now the
rapid-iteration model; earlier Wen results remain historical controls. Both help
prove the system that will support Codi and other models. The owner requests continued
hill-climbing once the loop works, with reviewed code and aggregate findings
published as the work proceeds.

**Current status:** ordinary native Wen weight updates, paired development
assessment, CPU tool loops in actual clients and the offline four-condition
harness auditor have been exercised. Six external clients have now completed
live MiniCPM model/tool exchanges; four passed the independently checked task
and two failed. BW's MiniCPM path and a complete interleaved live optimization
cycle remain unqualified. This document is the
implementation and experiment contract for that remaining work, not a result.

## Each harness learns its own improvements

BW, Codex, OpenCode, pi, Hermes, Qwen Code and DeepSeek Harness start from their
own pinned baselines. Each selected improvement study gets its
own general proposal, task proposal, separate probe executions and composed
version, based on that harness's own earlier behavior. Their changed surfaces
and exact content can differ. For example, one may need tool guidance, another
memory instructions, and another recovery or skill guidance. These are example
hypotheses, not measured conclusions.

The comparison holds the model, task objective, independent checks and declared
resource bounds fixed while preserving actual host semantics and permissions.
Do not force the same patch onto every client. Compare what helped each,
what failed, and which ideas transfer in an explicitly new test. The auditor
already binds each variant to its own harness, base and original observations;
the distinguishing test exercises different edit surfaces and rejects
substituting another harness's baseline as proposal evidence.

## One coupled round

**Current priority:** if at least two qualified harnesses pass a task, use them
as controls and improve BW to the same independently checked standard if it
fails. Four external clients already pass the initial MiniCPM discovery task.
Other harness optimization is discretionary when it teaches something useful
for BW or the learning loop. If all qualified stacks fail a task, inspect shared
inference and test foundations before attributing the failure to training and
skill coverage. Preserve negative observations and configuration repairs.

1. Freeze the starting model, candidate policy, source identities, each harness
   baseline, development tasks, protected transfer/retention cases, metrics and
   resource bounds before making requests. Record unavailable skill coverage.
2. Run the four-condition harness cycle separately for each harness using fixed
   weights: baseline, general probe, task probe, composed execution. Proposing
   and composing are additional model sessions. Editors see earlier observable
   behavior, never protected checker answers or future outcomes.
3. Freeze each harness's resulting recipe. Produce lessons from verified real
   work and separately generated owned practice. Include varied demonstrations,
   composition/recovery cases and balanced review across the covered domains.
   Keep protected questions and answers out of practice and editor inputs.
4. Train a new immutable candidate under a declared setting. Preserve its
   parent, exact examples/order, target masks, training/reload receipts and cost.
5. Cross-check both model versions through both configurations of each harness
   on the same protected cases. Retain original operations for already completed
   control cells; do not replay them under new IDs to fill a table.
6. Report gains, losses, errors and uncertainty by skill, gate and difficulty
   cell. Keep baseline quality, harness-only change, candidate-only change and
   their combined outcome visible. A candidate may interact differently with
   different harnesses. A global total cannot hide a lost domain.
7. Keep, repair or reject using the predeclared policy. Rejected candidates and
   their evidence remain research material. The current strict preservation
   policy is unchanged. No model or harness is automatically promoted.
8. Make an accepted version the next baseline and continue exploring remaining
   weaknesses, verified demonstrations, training settings, capacity and each
   harness's working methods. Preserve unsuccessful trials and resource costs.
   Continue within the active authorization; a plateau calls for a new declared
   hypothesis, not an unrecorded retry or a relaxed checker.

For **each** harness, the protected comparison has these four cells:

| | That harness's original configuration | Its own frozen improved configuration |
| --- | --- | --- |
| Original model | Original control | Harness effect with weights fixed |
| Trained candidate | Candidate effect with harness fixed | Combined result and interaction |

This is additional to the general/task development probes. The existing
`sss study harness` contract deliberately pins one model; do not insert changed
weights into it. Linked studies, actual host exporters and a checked joint
report are required before claiming that this table has been measured.

## Improve across the covered domains together

The owner approves larger mixed batches and slower steps when they help retain
and improve skills together. Each proposed update needs explicit coverage and
weights for new/failing classes, earlier skills and their compositions. Report
domain counts, unique underlying examples, repetitions, selected target tokens
and verification provenance. Repeated wording is not independent variety.

Increase review where a domain regresses, using fresh practice from that class;
do not train directly on a protected failed question. Test short development
screens during exploration and extended fresh checks for serious candidates.
Keep a sealed final assessment outside adaptive lesson and recipe selection.
Repeatedly optimizing against one development set can overfit it even when its
answers never enter training. Lack of a measured regression in a small sample
does not establish equivalence.

Start with the implemented, independently checked branches and expose missing
coverage. All-front improvement is an objective across declared covered
domains; it is not a claim that arithmetic tests establish administration,
tool use, code, long-context memory or research competence. Report individual
skills, composition and transfer/recovery separately, using the graph and four
difficulty coordinates rather than a single overall level or ranking.

Native ordinary backprop already accumulates examples one at a time before a
mean-gradient SGD update. A larger logical batch therefore does not require
all examples' activation graphs to coexist. It still costs more work and needs
admission for the actual model, gradients, per-example maximum sequence length,
workspace and device placement. Measure free memory and load on shared cards;
aggregate free VRAM is not automatically one usable pool. Standard full
backprop remains supported separately from experimental section-to-section
gradient passing. Current thinking-label policies remain explicit: verified
thinking plus actions/answers, or actions/answers only. Do not invent verified
reasoning spans by changing a flag.

## Seeds, evidence and allocation

Three distinct choices must be recorded: example-generation variation,
training randomness/order, and inference sampling. New varied examples from
the fixed recorded generator stream are allowed practice. They are different
from repeating the same experiment under multiple model seeds.

The inspected native full-update path has no configurable training seed,
dropout or automatic shuffling: it consumes explicit examples in order and
updates after the declared batch. Its LoRA initializer currently has a fixed
internal initialization. Merely adding a new seed label would not establish a
different experiment. Source: `experimental/native_training/native_train.cpp`
in the recorded PCC revision, including the ordinary update loop and initializer.

Research on BERT fine-tuning found that initialization and data order can affect
out-of-sample performance and that similar training losses can accompany
different test outcomes. See [Dodge et al.](https://arxiv.org/abs/2002.06305) and
[Mosbach et al.](https://arxiv.org/abs/2006.04884). These are reasons to measure
seed sensitivity when a genuinely stochastic recipe is qualified; they do not
establish a gain for Wen or make seed repetition a substitute for varied lessons.
Independent restarts measure robustness and produce separate candidates; their
learning does not automatically accumulate in one model.

The current campaign remains capped at 300 A100 allocation GPU-hours, charged
as stage wall time times allocated cards, including shared contention. Repeat
model runs with different seeds remain outside its authorization. Source,
aggregate outcomes, failures and costs should be published incrementally;
private traces, protected answers and machine handoffs stay private. Actual
host ledgers and PCC resource owners retain execution and settlement authority.

## Conditional release

The owner may later request export, download and Hugging Face publication if
the measured improvement is sufficient. That is a future release decision;
its improvement criterion remains to be agreed before final qualification.
Current candidates stay on the training host. No model transfer or upload is
authorized by a promising development result alone.

When explicitly authorized, select the recorded better candidate, merge any
active LoRA if applicable, and check the exact exported artifact for numerical
reload, quality and retention. Evaluate any quantization as a separate artifact.
Only then transfer the selected file and publish the supported claims and
limitations. Full updates and merged adapters must have correct lineage; do
not describe every updated checkpoint as a baked LoRA.

## Remaining completion evidence

- Live PCC-served Wen through qualified actual hosts, with effective settings,
  original operations, tool-result continuation, errors and resource receipts.
- Separate behavior-based proposer/probe/composer cycles for each harness.
- Larger varied, verified mixed-review training with immutable checkpoint and
  numerical reload agreement.
- The linked protected four-cell comparison across covered domains, including
  uncertainty, forgetting and model/harness interactions.
- At least a demonstrated useful improvement that survives independent checks,
  with a repeatable keep/repair/reject path another operator can run.
- Continued recorded hill-climbing within authorization and honest reporting of
  plateaus, failed candidates and unavailable coverage.

The current [paired assessment](WEN-PAIRED-ASSESSMENT.md) and
[real-client CPU proof](REAL-HARNESS-SETUP.md) are inputs to this work; neither
alone satisfies these completion requirements.
