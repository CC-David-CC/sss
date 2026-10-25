# Getting seven harnesses working with MiniCPM

An agent told us it had repaired a function, written the requested result, and
verified positive, negative, and zero inputs. Its checks looked good. The saved
function was still broken.

It had defined a corrected function inside a temporary Python command, used
that function to produce the right output, and tested another temporary copy.
The actual source file kept its original bug. A fresh checker loaded the saved
source and rejected the task.

Another agent repaired the source and produced the correct output, but changed
the input document it had explicitly been told to preserve. Four other
harnesses completed the same task and passed the independent checks. All used
the same MiniCPM weights. No training update occurred.

This is the story of getting the harnesses connected, and the useful failures
that appeared as soon as we checked their work.

## What actually ran

We connected six real external clients to the official MiniCPM5-2B F16 GGUF
through a native llama.cpp server. Each client kept its own prompts, tools,
schemas, execution loop, and output format. Each ran in a fresh isolated Linux
workspace on llm-49; the model ran on llm-60. The client could reach only the
granted model endpoint. It received no host credentials or general network
route.

The task required reading an input document, fixing an addition function,
writing a result derived from the input, verifying the function, and preserving
the input. Our separate checker examined the saved source, exercised additional
inputs, checked the written result, and compared the original input bytes.

| Harness | Observed result on this task |
| --- | --- |
| Codex 0.164.0 | Passed. Saved repair, correct result, preserved input. |
| OpenCode 2.1.4 | Passed. Saved repair, correct result, preserved input. |
| pi 1.4.0 | Passed after correcting its context declaration to 8K. |
| Hermes at revision `5894e750` | Passed after configuring a genuine 64K server slot and compatible launch settings. |
| Qwen Code 0.26.0 | Failed. Correct result and preserved input, but the saved function remained broken. |
| DeepSeek Harness 0.2.1-rc.2 | Failed. Correct source and result, but changed the protected input structure. |
| BranchWrite | Pending at this initial checkpoint; native integration and subsequent five-objective results appear below. |

These are observations from one task under fixed sampling, with configuration
repairs recorded separately. They establish different outcomes across these
stacks. They do not establish a general ranking, a failure percentage, or the
causal effect of a harness name. Prompts, schemas, protocols, context settings,
and tool implementations all differ. The server configuration also changed
during compatibility qualification, so these trials are unsuitable for a speed
leaderboard.

The [aggregate evidence](../validation/learning-program-20261024/minicpm-harness-discovery.json)
records model and client identities, the original receipt digests, individual
checks, and unsuccessful configuration attempts. Raw task material and traces
remain private.

## The fundamentals behind the difference

A harness helps determine what the model sees and what its output can do. The
same weights can receive different instructions, tool descriptions, conversation
history, and continuation messages. A valid-looking tool call can then have a
different effect depending on the tool implementation and its arguments.

Execution introduces another boundary: writing a correct function into a Python
command creates a function in that process. Persisting a repair requires changing
the source file. Testing the temporary function proves that temporary function
works. A later process importing the saved program can still encounter the old
bug. Qwen Code's observed trajectory demonstrated exactly that distinction.

Verification needs its own boundary too. Agents can misunderstand the task,
test the wrong object, or reinterpret a forbidden edit as a helpful cleanup.
DeepSeek's completed run described its input rewrite while also claiming the
input was preserved. The independent checker enforced the original requirement.

Context capacity has a client component as well as a model component. Pi's
pinned client subtracts a 4,096-token safety reserve before choosing its output
allowance. Declaring a 4K window led it to send `max_tokens: 1`; the first live
attempt produced no useful action. An 8K declaration allowed the task to finish
with unchanged weights. Earlier prompt-token measurements correctly showed that
the text fit within 4K, but that was insufficient to qualify the client's output
budget. The findings log preserves and corrects that interpretation.

Hermes introduced a different requirement: this pinned version enforces a
64,000-token minimum context for its custom-provider path. We provisioned actual
65,536-token slots rather than merely claiming a larger number in its config.
The task itself used much less context. That startup policy does not establish
that this task intrinsically needs 64K.

## Agent hype and our mandatory contribution to it

An impressive agent demo can end with a confident summary and some green checks.
The function may exist only in the terminal's imagination. Put a graph behind
the summary, call the retry loop self-improvement, and apparently we have solved
software engineering. The source file would like a word.

Having made fun of that pitch, we are obliged to supply our own. Satirical launch
copy follows:

> Introducing Skills³, the revolutionary agentic intelligence platform that
> transforms heterogeneous autonomous execution into verified capability
> convergence. Powered by the breakthrough discovery of reopening the file.

Our actual claim is smaller and useful: the machinery caught two plausible
completion claims that were wrong, while recording the successful runs too.
That gives us concrete behaviors to investigate and better controls for the
learning loop.

## Where BW and training fit

BW is the seventh harness and our primary improvement target. It owns user
tasks, tools, grants, and its task ledger. PCC owns native model execution,
branching context, model versions, training, and resources. S³ owns the skill
graph, independent scoring, practice selection, and regression evidence.

BW uses PCC's native branching-context protocol. Connecting an external client
to the llama.cpp API does not qualify that BW path. MiniCPM needs the appropriate
dense attention layout and tool-call handling there. Wen is also dense; its
hybrid recurrent/attention layout differs from MiniCPM's ordinary attention
layout. Expert routing is not the obstacle in this integration.

The current decision rule is practical. If at least two harnesses can complete
the task, use them as controls and improve BW to the same independently checked
standard if BW fails. Four external harnesses already provide passing controls
here. We can borrow useful methods without optimizing every external harness
for its own sake. If all qualified stacks fail a later task, first examine their
shared inference and test foundations, then investigate training and skill
coverage.

Harness improvements come before the next full-weight skill-training phase.
Training will use verified, varied lessons with mixed review, and separately
measure gains and losses. Fixed-weight harness changes and changed-weight
results remain distinct. A good anecdote earns an experiment; improvement
claims require broader transfer and retention evidence.

## Reproducible identities

The model is
[`openbmb/MiniCPM5-2B-GGUF`](https://huggingface.co/openbmb/MiniCPM5-2B-GGUF/tree/2079a22f3beaa4e306449978533478fe0522f4b3),
`MiniCPM5-2B-F16.gguf`, 5,039,006,688 bytes, SHA-256
`0ffba3682a853295566b98bc38c0ab755d6b2d91b994bc031ed727a08cfcdf25`.
The server used clean llama.cpp revision
[`972d2313`](https://github.com/ggml-org/llama.cpp/tree/972d2313bc0bf0a45f634f77d95c9fb03aeab12c),
including its native MiniCPM tool-call parser. Effective sampling was temperature
zero and seed zero, reasoning disabled, with at most 512 output tokens per
request. The broker recorded original and normalized requests separately.

Source pins, dependency locks, immutable request intents, API terminal events,
client events, isolated process settlement, and independent artifact checks
serve different purposes. Keeping those distinctions makes a failed run useful
instead of inconvenient.

## The next screen: correct files and a finished agent are different outcomes

The next comparison used five development objectives: Python empty-input handling,
first-match binary search, stable deduplication, shell filename quoting, and exit
status handling. All six clients declared 65,536 tokens and used actual native
slots of that size. Each execution had at most 12 model requests and 512 output
tokens per request. Sampling and weights stayed fixed. The shared A100 build
retained the previously recorded Wen naming patch; the runtime receipt includes
the exact binary and source-diff hashes. The patch is separate from MiniCPM
weights and is not evidence of a training change.

| Harness | Baseline completed | General advice | Task advice | Composed advice |
|---|---:|---:|---:|---:|
| Codex | 4/5 | 4/5 | 3/5 | 4/5 |
| OpenCode | 2/5 | 2/5 | 1/5 | 1/5 |
| pi | 3/5 | 1/5 | 0/5 | 1/5 |
| Hermes | 5/5 | 3/5 | 4/5 | 4/5 |
| Qwen Code | 4/5 | 4/5 | 2/5 | 3/5 |
| DeepSeek Harness | 4/5 | 3/5 | 3/5 | 2/5 |

Three real editor sessions per harness/task proposed general guidance, task
guidance, and a composition after observing the two probes. Editors saw redacted
behavioral events, not source solutions or independent grades. This produced
90 editor sessions and 90 new task executions alongside 30 baselines.

The completed-pass total fell from **22/30 to 15/30** after composition. However,
correct saved artifacts rose from **25/30 to 28/30**. Pi's task-specific probes
left correct artifacts on all five tasks yet completed none within the request
budget. More checking can improve a file while preventing the agent from
finishing. A hill-climber that scores only files would miss that cost.

We accepted none of these recipes. This was an exploratory test of appended
guidance, not every configuration surface supported by each harness. Five
objectives do not establish a general ranking. Transfer, retention and the full
formal comparison audit remain outstanding. The editor sessions used 121,401
input tokens and 12,179 output tokens; those are editor-only counts, not the
whole experiment's token bill. [Aggregate receipts and results](../validation/learning-program-20261024/minicpm-harness-development-screen.json)
preserve the distinctions.

## BW: fix the foundation before blaming the student

BW's native PCC integration exposed an ordinary but consequential porting bug:
PCC used Qwen's pre-tokenizer pattern for MiniCPM. Both tokenizers could round-trip
the same text, while producing different token IDs. MiniCPM groups digits in
runs of up to three and has different combining-mark boundaries. Its native
splitter applies two patterns sequentially; merging them into one expression
also disagreed on whitespace next to numbers.

The corrected Python path matched native llama.cpp on **2,438 token-ID
comparisons and all 130,560 vocabulary pieces**. Framing checks cover one root
BOS, appends after both native end tokens, thinking enabled/disabled, and
control-looking user text remaining ordinary data. Earlier BW trials remain
engineering evidence and are excluded from capability judgments.

BW now offers independent opt-in choices for direct constrained tool decoding
and compact instructions. With those choices and the corrected tokenizer, the
same original file task completed through BW's actual ledger, file/tool grants,
and native PCC context. The independent checker confirmed the saved function,
written result and unchanged input. That run used six model requests, 275 output
tokens and a 381-token initial controller prefix. Its observed wall time was
about 13 seconds on the RTX PRO 6000; this engineering sequence is not a speed
leaderboard.

The compact-prefix trials before tokenizer qualification also illustrate why a
host label saying verified is insufficient: the agent's chosen check passed,
while the independent checker rejected its result file. We preserved both
outcomes. [BW integration evidence](../validation/learning-program-20261024/minicpm-bw-native-integration.json)
records each trial separately. No MiniCPM weights were updated, and one successful
task does not establish broad BW mastery or justify a model release.

## BW's broader follow-up and native training mechanics

BW now has a five-objective native screen: three completed independent Python
passes, a quoted-filename timeout and a failure-status step-budget exhaustion.
The failure-status run used 13 requests: BW's limit was per action, not the
external screen's global 12-request cap. Do not compare these as equal-budget
causal scores. Input sentinels remained intact, and the original pending request
was reconciled as cancelled without replay.
[BW evidence](../validation/learning-program-20261024/minicpm-bw-foundations.json).

Codex, Hermes and Qwen passed the quoted-filename baseline; Hermes and dsh passed
the failure-status baseline. Those same-weight controls justify investigating BW
before assuming the model needs training. The root cause and fix are pending.

At that earlier mechanics checkpoint, PCC's opt-in ordinary-Llama trainer had
passed tiny full and LoRA scalar-gradient checks, F16/F32 loading, batching and
reload. Only SGD was implemented at that point, the final format guard still
needed exact CUDA requalification, and no real MiniCPM updates had yet occurred.
Those are historical facts, not the current implementation or learning status.
[The original mechanics evidence](../validation/learning-program-20261024/minicpm-native-training-mechanics.json)
is retained. Subsequent native AdamW/Muon work and measured MiniCPM learning are
reported in [the current native-learning report](MINICPM-NATIVE-LEARNING.md).

The early time-budget comparison is also historical. The current frozen study
compares equal practice exposure and records time as a measurement. Broader
AdamW ablations remain stretch goals. Mechanism, learning, retention and
acceptance remain separate gates.

## Shell diagnosis and follow-up

BW's original quoting run never executed its unfinished command. The other shell
run repeatedly tried writes through a read-only projection and direct execution
without execute permission. A broad controller rewrite regressed to two passes.
Retaining the old controller wording with clearer tool contracts/feedback gives
five correct saved artifacts and four completed independent passes; a further
completion-description change still does not finish the last task. All use the
same weights. No broad harness acceptance or model training is claimed.
[All variants](../validation/learning-program-20261024/minicpm-bw-shell-investigation.json),
[explanation](https://github.com/CC-David-CC/BranchWrite/blob/feat/minicpm-shell-feedback-20261024/docs/MINICPM-SHELL-INVESTIGATION.md).


## Check-readiness follow-up

Four same-weight five-objective BW probes returned 4/5, 4/5, 3/5 and 2/5
independently completed workflows. No proposed setting improved the default.
Some model-selected checks passed while the independently graded program was
wrong. [The BW experiment report](https://github.com/CC-David-CC/BranchWrite/blob/feat/native-learning-path-20261024/docs/MINICPM-CHECK-PROGRESS-EXPERIMENT.md)
separates actual check readiness, explicit completion and task correctness.
[The evidence](../validation/learning-program-20261024/minicpm-bw-check-progress-20261025.json)
retains runtime/source identities, bounds and individual outcomes. These five
discovery objectives are not a broad failure-rate study.


## October 25: compact receipts recover a repair, not a finished workflow

A new explicitly opt-in BW `compact-v1` tool-feedback presentation was compared
against omission of the option on the **same new BW source**. It removes repeated
model-visible plan/output hash renderings while preserving raw canonical
receipts, output/status/truncation, permission guidance, verification and
explicit-finish requirements. Both conditions kept the original MiniCPM5-2B F16
weights, one qualified native PCC profile, greedy sampling, 64K context and fresh
states. Paired instructions and independent checker commitments were identical.
No training or model update occurred in this probe.

| Measurement | Baseline | Compact |
| --- | ---: | ---: |
| Correct saved artifacts | 4/5 | 5/5 |
| Completed independent passes | 4/5 | 4/5 |
| Whole-workflow model calls | 36 | 39 |
| Generated output tokens | 1,857 | 2,231 |
| Newly supplied tool-feedback tokens | 16,399 | 11,522 |
| Native forward tokens | 30,811 | 26,347 |

The first four objectives passed both gates in both conditions. On the remaining
failure-status objective, baseline repeated one exploratory shell call ten times
without editing, checking or finishing. Compact saved a correct repair and
reached four named checks, then kept checking instead of requesting finish.
Both exhausted 256 interpreter steps after 13 model calls. Compact remains
experimental and opt-in; this is not an accepted termination fix.

Live feedback tokens fell 29.7%, but calls and generated output increased. The
14.5% lower native forward-token count comes from different trajectories and
does not establish a speedup or lower overall compute cost. A separate CPU
measurement rendered the same 12 saved messages both ways and found 38.1% fewer
tokens; that measures presentation directly rather than autonomous behavior.

The new-source baseline did not reproduce the historical control's correct
saved repair. Source-bound operation IDs and hash-bearing feedback can change
when BW source changes, so earlier source trials are not interchangeable causal
controls. These are five original development objectives, one run per condition,
not a general failure-rate, mastery or unseen-transfer study. The 12-request
limit remains per model action, not global; the 120-second task guard, 512 output
tokens per request and 256-step limit were identical across this pair.

[Aggregate evidence and definitions](../validation/learning-program-20261024/minicpm-bw-compact-feedback-20261025-bh.json)
include model/native/code/grader hashes, independent artifacts and actual
explicit-finish outcomes. [BW's report and reproduction protocol](https://github.com/CC-David-CC/BranchWrite/blob/feat/compact-tool-feedback-20261025/docs/COMPACT-TOOL-FEEDBACK.md)
describe fresh-state construction, independent grading and uncertain-operation
handling without exposing raw tasks or solutions. A post-run full manifest audit
recorded three concurrent S³ Markdown edits; runtime and grading source, native
dependencies and weights were unchanged. The original manifest was preserved.
All 105 native journals settled; the owned inference server and child stopped,
its port closed and the GPU lease was released.

This result belongs to fixed-weight harness development. The separate
[native-learning comparison](MINICPM-NATIVE-LEARNING.md) measures changed model
weights, learning and forgetting. Neither experiment should take credit for the
other's improvements. Fresh transfer and reliable explicit completion are still
required before adopting compact feedback as a default.
