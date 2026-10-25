# Skills³ (S³)

[LoRA rank extension: 1, 2, 3, 4, 8 alongside 16](docs/LORA-RANK-EXTENSION.md) adds five independent 68-update arms with the same frozen practice and questions. First results are pending.

[The durable learning loop: ELI5, master's, PhD, and applied guide](docs/LEARNING-MACHINERY.md) explains ownership, recovery, paired learning/forgetting, expanding assessments, commands, and current qualification limits. The new machinery checks are separate from the fixed 68-update comparison.


[Eight-update optimizer geometry](docs/OPTIMIZER-GEOMETRY.md) compares saved
weight spectra with matched learning and forgetting. [Check sensitivity](docs/CHECK-SENSITIVITY.md)
uses actual BW execution to distinguish a passing command from a check that
detects declared bugs. Both preserve negative controls and unfinished acceptance.

Current work uses equal update counts and ordered practice; the older fixed-compute
preparation above is historical. S3's [shared COW evaluation path](docs/COW-EVALUATION.md)
uses the same native request implementation as BW. PCC carries the
[small-probe speed result](https://github.com/CC-David-CC/Private_Context_COW/tree/feat/native-learning-curves-20261024#48x-faster-on-small-forward-work-probes);
S3 owns the test method, paired scores and learning/forgetting evidence.

[Earlier MiniCPM Muon/AdamW mechanics](docs/MINICPM-OPTIMIZER-PILOT.md): full-weight
updates and reload pass; resumed Muon weights/moments match uninterrupted training
bit for bit. That pilot is mechanics evidence; the later matched-practice learning
and forgetting measurements are linked below.

[What we are discovering](docs/FINDINGS.md): readable findings about context
cost, tool differences, training, forgetting and practical next steps.

[Getting seven harnesses working with MiniCPM](docs/MINICPM-HARNESS-FIELD-NOTES.md):
six external clients completed live model/tool exchanges with the same weights.
Codex, OpenCode, pi and Hermes passed independent artifact checks; Qwen Code
and DeepSeek failed different task requirements. BW's shell-contract follow-up reaches 5/5 correct saved artifacts and 4/5 completed
workflows; one verification/termination failure remains. See [BW's measured
investigation](https://github.com/CC-David-CC/BranchWrite/blob/feat/native-learning-path-20261024/docs/MINICPM-SHELL-INVESTIGATION.md). This is one discovery task, not a general harness ranking.

[Four-condition harness comparisons](docs/HARNESS-COMPARISON.md) have tested
offline planning and evidence checks. [Isolated model transport](docs/MODEL-SOCKET.md)
keeps actual client tools and private receipts separate from task grading. [Wen's full-update pilot](docs/WEN-FULL-UPDATE-PILOT.md)
changed the protected score from 17/54 to 19/54, with three gains and one
regression. The candidate was rejected and was not promoted. A larger
[paired assessment](docs/WEN-PAIRED-ASSESSMENT.md) found place value improved
from 23/96 to 29/96, with seven gains and one loss; 96 review outcomes were
unchanged. Uncertainty and the original rejection remain explicit.
[Joint learning and harness hill-climbing](docs/JOINT-LEARNING-LOOP.md) records
the next live cycle, per-domain controls and conditional release gate.
Development checkpoint: [foundations and workflow validation](validation/foundations-20261023/README.md). Broader skill qualification and MiniCPM learning/retention remain pending.


**New foundations preview:** [Start here](docs/START-HERE.md), [on-disk skill graph](docs/ON-DISK-LAYOUT.md), [operator handoff](docs/OPERATOR-HANDOFF.md), and [implementation gates](docs/FOUNDATIONS-PLAN.md). The reference machinery and model mastery are reported separately.

**Skills, Scoring, Stability.** Know what an assistant can do, teach it something
new, and check that it still remembers how to do its other jobs.

Repository and Python import: **`sss`**. Distribution: **`skills-cubed`**.
Say **“Skills cubed.”**

S³ is an independent project. A model server or an app can import its skill tree,
tests, scoring and practice curriculum. It is intended to support a useful
coding and Linux administration assistant, with basic reasoning underneath.

| Part | Responsibility |
| --- | --- |
| **Strata core** | Run supported models and provide native computation. |
| **COW / PCC** | Manage model context, versions, native training and resources. |
| **BranchWrite** | Handle user tasks, files, tools, grants and the canonical task ledger. |
| **S³** | Define skills, evaluate evidence, detect regressions and choose mixed practice. |

S³ does not grant shell access, replace BW's workflow runtime, or promote a model
by itself. Its model-only benchmark executes calls against isolated mock files;
host adapters use the real runtime and its receipts. A skill score never grants
a capability.

## The tree we want

- **Tool-use foundations:** read, write, edit, finish; arguments; interpreting
  outputs; multi-step dependencies; recovering from failures; respecting scope.
- **Linux administration:** services, logs, processes, storage, permissions,
  networking, configuration, packages and owned GPU jobs.
- **Coding:** understanding code, making bounded changes, writing scripts,
  testing and reviewing the result.
- **Supporting reasoning:** arithmetic, units, paths, quoting and instructions.

The broad map marks model proficiency **unmeasured**. Available tools are not
proof that a model uses them well. The legacy configured training adapter covers
five integer-arithmetic skills. The progressive-graph training preview activates
nine math/state skills with their prerequisites. Linux and coding packs need
their own model trials and owned execution fixtures; they are not silently
marked passing.

## What exists now

- A versioned tree with required practice, validation and blind coverage on every
  active leaf. Missing results never count as passes.
- Preservation checks for individual questions. A gain elsewhere cannot hide
  losing a previously correct answer.
- A bounded curriculum that interleaves focused lessons and replay from other
  skills. A regression changes the next round's practice priorities.
- Separate practice and evaluation inputs, including token-level overlap checks.
  Failed test questions do not become LoRA labels.
- Nine original tool-use scenarios and deterministic host-trace graders covering
  reading, writing, editing, verified completion, recovery and file scope.
- Optional PCC and BW integration fixtures using real tool boundaries, HTTP
  requests and native CPU updates. Their injected skill outcomes prove wiring,
  not model competence.

Guarded jobs have a frozen policy, explicit step budget and maximum round count.
Blind evaluation runs after validation qualifies; a blind failure rejects the
candidate rather than becoming another adaptive teaching round. Candidates
remain unpromoted. Interrupted jobs retain their original identities and are
not blindly replayed.

**First real model comparison:** Wen 1 passed **5/9** and Wen 1.1 **4/9** on the
same bounded mock-tool suite/A100. The extra 1.1 failure was a correct read answer
without the required finish action; shared newline failures have unresolved
model/parser attribution. These are strict stack scores, not a general model
ranking. [Read the case-by-case report and limits](docs/MODEL-COMPARISON.md).

The completed five-skill native mixed-practice pilot preserved earlier successes
but stayed at **14/40** held-out checks after four rounds/16 updates. No hat
qualified. [Full learning evidence](validation/README.md).

The new progressive-graph pilot has completed 18-example/one-update and
108-example/18-update experiments across nine skills. Both stayed at **17/54**
protected checks, with zero gains or regressions. The larger LoRA candidate
passed serving and native reload checks, but did not qualify.
[Current foundation pilot and its limits](docs/FOUNDATION-TRAINING-PILOT.md).

## Try it

The core uses Python 3.11+ and the standard library. It needs no model or GPU.

```sh
git clone https://github.com/CC-David-CC/sss.git
cd sss
python -m pip install -e .
sss tree
sss suite tool-use
python -m unittest discover -s sss_tests -p 'test_*.py'
```

The native/BW integration tests are separate and require matching host checkouts.
See [integration and ownership](docs/INTEGRATION.md),
[the skill map](docs/SKILL-MAP.md), and [measured status](validation/README.md).

For the complete explanation of the tree, scores, teaching loop and limitations,
read [the S³ user guide](docs/USER-GUIDE.md). Model comparisons and historical
hardware results belong in [the benchmark report](docs/MODEL-COMPARISON.md).
The [benchmark procedure](docs/BENCHMARKING.md) explains how to run the same
bounded tool tasks against two models without giving either access to your PC.

An application can import the core without importing a model runtime:

```python
from sss import SkillTree, SkillGuardRunner
from sss.catalog import catalog
from sss.suites.tool_use import scenarios, grade
```

## Inspiration and provenance

**Strengthened by ideas incorporated from [LearnHarness](https://github.com/amosblomqvist/learnharness).**
Its teaching design inspired S³’s new, independently checked joint-premise,
premise-change, reverse-support and method-selection exercises. Skill
prerequisites, lesson arguments and measured mastery stay separate.
[Try the reasoning curriculum and delayed archive revisit](docs/REASONING-CURRICULUM.md).

[SeraphimSerapis/tool-eval-bench](https://github.com/SeraphimSerapis/tool-eval-bench)
informed the tool-use categories: tool selection, precise arguments, dependency
chains, read-before-write, recovery and truthful completion. Its mock-tool scope
does not establish whole-agent or Linux-administration competence. S³'s initial
file scenarios and graders are newly written around host-supplied evidence.
See [references and credit](docs/REFERENCES.md).

The first tree/guard and arithmetic-study code was extracted from PCC and BW
development work. Their runtime APIs stay in those projects; the curriculum and
tests live here. Raw private traces, model weights and operational handoffs stay
outside this repository.

## Current learning evidence

[Learning and forgetting graphs](docs/COW-SHARED-ROOT-LEARNING.md) plot measured
correct answers, stopping, answers gained and original successes lost against
update count. Four full-weight regimens continue toward 68 updates with the same
ordered practice stream. A separate [attached-LoRA series](docs/MINICPM-DIRECT-LORA-LEARNING.md)
reaches **231/864 correct and 781/864 naturally finished after three updates**,
from 59/415 originally: 173 answers gained and one original success lost.
Native adapter reload and bounded independent-oracle checks pass; merged-model
parity remains a separately retained failure. These are repeated development
measurements, with sealed acceptance and broader skills still unfinished.

Earlier adaptive checkpoints and their results remain separate from this
original-model control study. The first AnswerStop candidate reached 482/864;
later mixed-review work reached 507/864. Regressions are recorded, promising
exploratory checkpoints are preserved, and a score alone does not authorize
promotion. See [the full learning record and native HTTP/CLI block](docs/MINICPM-NATIVE-LEARNING.md).
Broader optimizer ablations remain stretch goals.

[Original/trained execution comparisons](docs/COW-FIRST-DATA-BLOCK.md) matched
all 864 sampled sequences in each pair. Observed evaluation ratios were 6.1x
(original A100), 2.7x (trained A100), 5.3x (original llm-60) and 2.2x (trained
llm-60), with shared-load and scope limits. S3 uses PCC's existing consumed COW
request, the same underlying request BW uses; these direct-answer panels are
separate from BW tool-workflow qualification.

[Earlier fixed-compute preparation](docs/FIXED-COMPUTE-PREPARATION.md) is retained
as history. Update counts and practice exposure organize the current comparison;
wall time is a measured cost.

[Resolve a recommended parent](docs/RESOLVED-LEARNING-PARENT.md) against actual
PCC artifacts before another update. The optional bridge recomputes the saved
S³ proposal and preserves exact identities without dispatching training.

[Registered LoRA AdamW through BW and COW](https://github.com/CC-David-CC/Private_Context_COW/blob/feat/native-learning-curves-20261024/docs/REGISTERED-LORA-ADAMW.md) now has real CPU checks and a short MiniCPM A100 qualification through both actual clients. Resumed and uninterrupted GPU updates produced identical adapter and optimizer-state file hashes. It is explicit and optional; existing default training recipes are unchanged.

The [current learning and forgetting graph](docs/COW-SHARED-ROOT-LEARNING.md) contains 118 scored checkpoint positions, including an equal-practice comparison at update 19 and the observed LoRA setback at update 24. These are continuing development trajectories, not a completed optimizer ranking or accepted model release.

[Owner-configured COW learning](docs/CONFIGURED-COW-LEARNING.md) now has a two-round actual MiniCPM machinery qualification through both BW and COW clients. The 15-case panel demonstrates the workflow, with broad acceptance still separate.
