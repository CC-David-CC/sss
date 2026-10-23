# Using Skills³

**S³ answers three questions: what can the assistant do, did this attempt work,
and did teaching it something new damage something it already knew?** It is the
shared skill map, test collection, scoring and mixed-practice machinery for PCC
and BranchWrite. You can use its core independently of either project.

## Where each part belongs

Imagine asking your assistant to repair a broken service configuration.

1. **BranchWrite** receives your task, asks permission through its configured
   grants, reads the files, runs allowed tools and records what actually happened.
2. **PCC** runs the selected model and manages its context. Its modified Strata
   core serves supported Flash models; the optional dense adapter serves Wen and
   Qwen3.5. PCC also owns native training and immutable model/adapter identities.
3. **S³** identifies the skills involved and grades independently checked
   evidence. It can tell an owner-configured training job which practice skills
   need attention and which previous successes must be preserved.

A model saying “fixed” is not a passing result. A tool existing is not a learned
skill. A training loss going down is not proof of useful learning.

## The tree and its primitives

The broad catalog starts with **read, write, edit and finish**. Read means obtain
the actual input. Write means create the requested new material. Edit means
make a bounded change to an observed existing object. Finish means check the
result and report truthfully, including when the task failed.

Those foundations support argument accuracy, interpreting noisy outputs,
dependent steps, scope and recovery. Linux administration builds on those:
inspect a service, read its logs, understand its configuration, propose a bounded
repair, run the relevant check, then verify the actual service. Coding follows
the same pattern with source, edits and tests. Arithmetic, units, paths and
quoting support these jobs; arithmetic alone does not make an administrator.

Run `sss tree` for the broad catalog. Its proficiency entries are currently
**unmeasured**. A configured PCC server's active training tree is smaller and
bound to its exact model contract. Inspect that with `branchwrite lesson skills`
or the PCC client's `lesson skills`. Do not interpret the broad catalog as an
already trained model or an implemented Linux curriculum.

An active leaf needs owned **practice**, **validation** and **blind** coverage.
The initial native-training adapter covers add, multiply, absolute value, floor
and ceiling. Nine separate tool fixtures cover reading, creating, editing,
checked completion, recovery, scope, noisy data, dependent actions and exact
paths. A generic checker contract allows more domains, but each needs a real
evaluator and appropriate fixtures before activation.

## How a score becomes evidence

S³ grades completed observations, not the assistant's explanation of them.
File tests compare actual final contents and required reads. Completion tests
require a passing check after the final mutation. Recovery tests require a
failed check followed by a passing one. Missing or unsettled tool effects are
**unavailable**; they must not be converted into a model failure or a pass.

The model-only tool benchmark uses virtual files and deterministic mock checks.
It measures tool selection and sequencing through real model inference, without
running shell commands or touching project files. This is useful early evidence,
but real BW tasks, service administration and native numerical correctness each
need their own execution tests. See [the benchmark procedure](BENCHMARKING.md).

Preservation is checked per question. If a candidate gains ten successes but
loses one protected earlier success, the new average cannot conceal that loss.
Every required result must be present. Missing coverage is not permission to
lower the bar. Results are meaningful only with their model, suite, checker,
execution settings and resource budget recorded.

## Teaching a checked lesson

A task may fail, receive help, then pass independent checks. BW can record the
checked correction as a lesson with a skill tag. An enabled PCC training service
can consume one lesson now or an explicitly selected batch later. It can create
a new LoRA “hat,” continue a compatible qualified hat, or perform direct full
weight updates. Native C++/GGML training does not require PyTorch.

S³'s optional guard first measures the original model or qualified parent. It
then interleaves new/focused practice with replay from the other active skills.
After each bounded round it checks the whole active validation tree. Weak or
regressed skills influence the next round's practice selection. It never copies
a failed evaluation question into the training batch.

For example, a 32-example round with batch size eight takes four updates. A
16-update job with a four-round policy can consume at most 128 example slots.
Each active skill appears in each round; focused practice cannot eliminate
replay. Examples may recur across rounds, so consumed slots must not be called
distinct examples. The original requested lessons are consumed in round one.

Once validation qualifies, the guard compares the original and candidate on the
blind split. A blind failure rejects the candidate; it does not start another
adaptive teaching cycle using those blind answers. Exhausting the round/step
budget also leaves the candidate unqualified. Even a qualified candidate is
**not automatically promoted** to the model serving your tasks.

This does not promise that an always-worn hat improves forever. The earlier
single-skill Wen experiment is a useful warning: excellent gains on one wording
family coexisted with retention failures and weak blind generalization. Mixed
practice and regression gates provide a way to test the proposed remedy, not
proof that the remedy has already produced a better general assistant.

## Use just the setup you own

The S³ catalog, graders and core tests need only Python 3.11+ and no GPU. CPU
integration fixtures can establish that lessons, batches and native updates are
connected correctly. They do not establish language-model learning quality.

Model trials require a supported PCC backend and enough available resources for
the particular model/profile. An R730 with two P4s, a 7900 XTX, a 4090, a PRO
6000 and a shared A100 have different supported routes and evidence. Read
[PCC's hardware guide](https://github.com/CC-David-CC/Private_Context_COW/blob/main/docs/START-HERE.md)
before downloading. Owning one setup is sufficient to use the parts qualified
there; the skill tree never assumes access to the whole fleet.

On shared GPUs, PCC owns device selection and leases. S³ does not combine
fragmented free VRAM, evict other users, or make unsupported backends compatible.
Ordinary full-graph backprop is the default training path. Passing adjoints
between independently executed model sections remains a separate experiment.

## What to read and run

- [Installation, host integration and lesson commands](INTEGRATION.md).
- [The broad skill map and missing coverage](SKILL-MAP.md).
- [How to reproduce a bounded model-only tool comparison](BENCHMARKING.md).
- [Model comparisons, historical Flash evidence and limitations](MODEL-COMPARISON.md).
- [Validation evidence](../validation/README.md).

Do not send private task traces, credentials or protected evaluation answers to
the public repository. Keep immutable raw evidence privately; publish reviewed
aggregate results with the provenance needed to understand them.
