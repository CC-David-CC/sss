# What we are learning while building the learning loop

Updated 2026-10-24 UTC. This is the human-readable findings log for S³, BW and
PCC. Keep useful failures, surprises and practical implications alongside gains.
Each entry states the measured scope; a development observation is not a model
qualification. Add new evidence without erasing earlier outcomes.

## 1. The same file workflow has very different prompt overhead

Using **Wen 1.1's actual tokenizer and PCC formatter**, these captured client
conversations had four scripted tool calls and five requests each:

| Actual client | Prompt tokens across the five requests | Context needed for this capture, including 512 output tokens |
| --- | ---: | ---: |
| Codex 0.164.0 | 8,271–8,840 | 16K = 16,384 |
| OpenCode 2.1.4 | 1,655–1,987 | 4K = 4,096 |
| pi 1.4.0 | 1,434–1,731 | 4K = 4,096 |

**Why this is useful:** a small context can prevent a task from even reaching
the model. PCC correctly refused all five Codex requests at the old 8K pilot
capacity. OpenCode and pi's captures fit. These counts establish prompt cost
for these versions, tools, settings and captured conversations, not universal
minimums or a quality/speed ranking.

**Action:** preflight real requests, then qualify a common 16K hardware profile
for the next live comparison. Longer live trajectories may need more. Wen's
declared maximum remains 131,072 tokens; these CPU counts do not qualify that
capacity on a GPU. [Procedure and positive/refusal evidence](REAL-HARNESS-SETUP.md#preflight-wens-actual-tokenization-before-gpu-work).

## 2. Similar tool names can hide different argument formats

OpenCode 2.1.4 uses `path` for its file tools and calls its command tool `shell`.
pi 1.4.0's edit tool takes an `edits` list. Assuming older examples' formats made
the first protocol probe fail. The actual advertised schemas identified the
problem; corrected requests passed.

**Action:** pin the client and inspect its actual schema. Teach and test the
format the target harness expects. A failure to call a tool correctly may be a
compatibility issue rather than missing reasoning ability. These failures were
in our fixture requests, not Wen outputs. [Actual-client evidence](REAL-HARNESS-SETUP.md).

## 3. A successful program exit does not prove the task succeeded

In the first probe, pi returned exit code zero after the fixture encountered a
protocol error. The independent checks still rejected the workflow. The final
proof required the edited program, written notes, four actual tool calls and
the tool results appearing in subsequent requests. All three clients then
passed, with all disposable process boundaries settled.

**Action:** check artifacts and observed effects, not just an agent's final
message or process exit status. [Validation](../validation/learning-program-20261024/real-cli-transport.json).

## 4. PCC already has the protocol needed by this Codex client

The pinned Codex client uses Responses. PCC already implements Responses input
parsing, tool-name mapping and streaming output. The actual Codex client
completed a five-request file/tool loop through those real PCC protocol
functions in an isolated CPU test.

**Action:** qualify the existing path against Wen before adding a new backend.
That CPU proof used scripted replies; it did not call PCC's native model engine.
BW continues to use its native COW context protocol. [Scope and setup](REAL-HARNESS-SETUP.md).

## 5. One changed answer can give a misleading impression of a whole skill

The first full-update pilot lost one place-value success: 3/6 became 2/6. A
larger fresh paired sample then showed 23/96 becoming 29/96, with seven newly
correct answers and one newly wrong answer. Both findings remain valid for
their respective cases; the larger result does not erase the lost example.

**Action:** investigate a suspected regression with varied paired cases before
concluding that the entire class declined. The new suite also corrected a
composition generator, so its absolute score is not interchangeable with the
old suite. [Larger assessment](WEN-PAIRED-ASSESSMENT.md).

## 6. The larger sample is encouraging, but the improvement is not settled

Place-value failure fell from 76.0% to 69.8%, a measured 6.25-percentage-point
decrease. Seven gains versus one loss give an exact paired two-sided McNemar
p-value of 0.0703125. Independent passes improved 9/32 to 12/32; composition
4/32 to 7/32; transfer/recovery stayed 10/32. On the other 96 review questions,
both models passed the same 36 cases. Absolute performance is still low.

**Action:** keep the candidate for research, strengthen varied practice and
review, and test fresh transfer and retention. The candidate remains
unpromoted. Twelve review questions per other skill cannot prove general
retention; 96 primary questions do not settle a small improvement either.
[Counts, uncertainty and limitations](WEN-PAIRED-ASSESSMENT.md).

## 7. Training loss can improve before measured task success does

The earlier rank-four LoRA pilots changed no pass/fail outcomes on the 54-case
development suite: this held for the 18-example update and the later
108-occurrence, 18-step run. The single full-weight update on the same original
18 examples reduced practice loss from 0.4352 to 0.2651 and changed the score
17/54 to 19/54, with three gains and one loss.

**Action:** report task outcomes and forgetting alongside loss. This is not
evidence that full updates are generally superior: the LoRA and full runs used
different learning rates and were small pilots. [LoRA history](FOUNDATION-TRAINING-PILOT.md),
[full-update evidence](WEN-FULL-UPDATE-PILOT.md).

## 8. Larger logical batches need more work, but not all activation graphs at once

The inspected native standard-backprop loop accumulates examples one at a time,
then applies a mean-gradient SGD update. Each example has its own temporary
graph; the parameter gradients persist until the update. Thus increasing the
logical batch need not multiply simultaneously resident activation graphs by
the example count.

**Action:** try larger varied mixed-review batches while admitting actual
maximum sequence length, model/gradient storage and workspace on each device.
This code property does not establish that an arbitrary batch, long sequence
or collection of free VRAM fits. The longer mixed-batch learning experiment
still needs measurement. [Training plan](JOINT-LEARNING-LOOP.md#improve-across-the-covered-domains-together).

## 9. Saving in FP32 almost doubled this checkpoint's disk size

The original BF16 Wen file is 16,244,817,856 bytes. The full-update writer saved
active tensors in F32, producing 31,876,841,504 bytes, about 31.88 GB decimal.
This is a precision/storage change, not a doubling of model parameters.

A separate native reload measured practice loss within about 1.6×10⁻⁸ of the
saved candidate's recorded value. No update occurred during that reload.

**Action:** budget checkpoint disk space by saved precision and verify reload
before expensive evaluation. Numerical reload agreement does not establish
better task performance. No GGUF has been transferred back or uploaded.
[Exact measurements](WEN-FULL-UPDATE-PILOT.md#savereload-and-resource-evidence).

## 10. More shared VRAM does not automatically form one training memory pool

Different cards have different free memory and competing compute load. Ordinary
native full updates have been exercised across four shared A100s, while the
paired serving assessment used one card at a time. Resource admission must use
the actual placement and fresh per-card measurements.

**Action:** include gradients, activations, workspace and reserves, not just
weight size or the sum of free VRAM. Keep experimental gradient passing between
model sections distinct from ordinary full backprop. [Full-update scope](WEN-FULL-UPDATE-PILOT.md).

## 11. GPU-hours count allocated cards, even while the server is shared

Four allocated cards for 15 minutes cost one allocation GPU-hour. The complete
one-update pilot cost 0.6216 GPU-hours; the larger paired assessment cost 0.4803.
Shared contention affects elapsed time, so these are not dedicated-server
throughput benchmarks.

**Action:** charge stage wall time times allocated cards, settle leases and
report failures' costs too. Allocation-hours, free VRAM and utilization answer
different questions. [Pilot accounting](WEN-FULL-UPDATE-PILOT.md),
[assessment accounting](WEN-PAIRED-ASSESSMENT.md#resources-and-audit).

## 12. Our own duplicate lock looked like unavailable infrastructure

The first expanded-assessment attempt took the GPU lease that PCC itself needed
to acquire. PCC then refused to start. Zero questions were answered; the failed
attempt settled and cost 28.4175 GPU-seconds. The corrected operator used a
separate lifetime lease and preserved the original failed attempt.

**Action:** diagnose resource ownership before treating an unavailable service
as a model failure or starting another job. A leftover lock file alone does
not establish a live owner. [Failure and correction](WEN-PAIRED-ASSESSMENT.md#resources-and-audit).

## 13. A label saying “composition” did not make the old test compositional

Preparing the larger sample exposed place-value cases labeled composition that
still asked directly for a digit of a supplied number. Version 2 requires
calculating a nested expression before selecting a digit from its unprovided
result. Its checker independently validates the expression/result relation.

**Action:** inspect what a generator actually requires. Preserve source pins and
historical results when fixing coverage; do not silently regrade them under a
new definition. [Generator correction](FAILURE-RATES.md#correcting-composition-coverage).

## 14. Harness improvements and weight improvements need separate controls

The 17/54 to 19/54 result came from changing weights while keeping serving and
checks fixed. The client compatibility work did not produce that gain. Each
harness may need different improvements; a future joint study must measure
both models through both that harness's original and optimized configuration.

**Action:** report strengths and weaknesses by domain, composition, context,
environment and autonomy, with costs and failures visible. Look for model/harness
interactions instead of assuming one best universal patch or ranking. The
complete live interleaved loop is still unqualified. [Joint comparison and
continued hill-climbing](JOINT-LEARNING-LOOP.md).

## 15. Changing a seed label would currently do nothing useful to a full update

The inspected native full-update path consumes explicit examples in fixed order
and exposes no configurable training seed, automatic shuffling or dropout.
Its LoRA initializer has a fixed internal initialization. Independent stochastic
restarts, when available, test sensitivity and produce separate candidates;
they do not automatically accumulate their learning into one model.

**Action:** prioritize varied verified lessons, mixed review and declared
training-setting changes now. Distinguish example-generation variation,
training order/randomness and inference sampling. The current campaign still
excludes different-seed model repeats. Broader seed research and the precise
scope of that restriction are recorded in the
[joint-loop guide](JOINT-LEARNING-LOOP.md#seeds-evidence-and-allocation).

## 16. Ordinary full backprop is working through the native engine

The full-update pilot used native C++/GGML training, without PyTorch, and
reported finite nonzero gradients for all 427 active parameter tensors. It
saved an immutable candidate and passed the separate measured reload check.
This is ordinary full-graph backprop, distinct from experimental gradient
passing between separately managed model sections.

**Action:** use the tested standard path as the control while qualifying larger
curricula. The result establishes this bounded training mechanism, not success
on arbitrary model architectures or long training sequences.
[Native update evidence](WEN-FULL-UPDATE-PILOT.md).

## 17. Training only answer labels does not freeze the preceding context

Selecting actions/answers as loss targets differs from cutting the computation
graph. Gradients can still flow through the context that produced those tokens.
Adding thinking tokens as explicit targets is another choice, and requires
verified reasoning spans rather than unexamined generated thoughts.

**Action:** record inference thinking, training target masks and backprop mode
separately. A “thinking off” label alone does not describe all three. Current
Wen pilots used actions/answers targets; verified thought-target training still
needs its own qualified examples. [Operator contract](OPERATOR-HANDOFF.md).

## Keep this log useful

For each new finding, record the exact model/client/source and tested workload,
the observation, why a person should care, a concrete next action, evidence and
limits. Include negative and unchanged results. Correct an interpretation by
adding the new evidence; preserve the original measurement. Release remains a
later owner decision after sufficient improvement and exact-artifact checks.
