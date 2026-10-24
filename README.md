# Skills³ (S³)
Development checkpoint: [foundations and workflow validation](validation/foundations-20261023/README.md). Live-model qualification remains pending.


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
proof that a model uses them well. The current executable training starter tree
covers five integer-arithmetic skills. Linux and coding packs need their own
model trials and owned execution fixtures; they are not silently marked passing.

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

The new progressive-graph pilot has also completed one real 18-example update
across nine skills: protected checks stayed at **17/54**, with zero gains or
regressions. The LoRA candidate was served successfully but did not qualify.
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
