# A learning loop that remembers what it actually did

This page explains the new opt-in learning-run machinery across **Skills³
(S³), BranchWrite (BW), and Private Context COW (PCC)**. It is a development
pathway for an owner or an agent to drive and inspect. The small CPU integration
fixture passes, and the owner-configured actual MiniCPM COW path has completed
two native learning rounds through both real CLI clients. This qualifies the
measured machinery, not broad capability or release acceptance. The existing fixed 68-update optimizer comparison keeps its original
questions, practice order, and execution snapshots.

## ELI5: give the experiment a notebook

Imagine teaching a student, checking their homework, and writing down what to
practice tomorrow. If the computer crashes, we need to know which student
version took which lesson and whether the lesson actually finished. Otherwise
we could accidentally teach it twice, test an old version, or lose a useful
improvement.

PCC keeps that notebook beside the actual training jobs. BW gives a person or
an agent controls to read it and request the next step. S³ checks the answers,
records what improved and what was forgotten, and recommends the next practice.
An uncertain result stays uncertain until someone resolves it.

The tiny integration student went **0/4 → 2/4 → 4/4 → 4/4**. The system kept
the two improvements, then kept the previous working parent when another round
produced no measured gain. Those are four synthetic classification questions.
They demonstrate the machinery; they do not establish MiniCPM's intelligence
or its maximum ability.

When a real adaptive learning panel becomes too easy, we should ask more unseen
questions and eventually harder ones. We keep the old questions as anchors and
give every model being compared the same new questions. We do not change the
questions partway through the fixed 68-update comparison.

## Master's level: the engineering contract

The main problem is preserving identity and ownership across a sequence of
side effects. A run must bind the original model, the current working parent,
verified lessons, an owner-registered training recipe, native job receipts,
evaluation evidence, and the resulting decision. A high score attached to the
wrong weights is unusable evidence.

| Component | Owns |
| --- | --- |
| Modified Strata core inside PCC | Supported model computation and native gradients/updates. |
| PCC/COW | Model and candidate identities, admitted training, resources, durable run/round records, native receipts, and private exports. |
| BW | User tasks and its existing workflow ledger; journaled requests to PCC and controls for a human or agent. |
| S³ | Skills, independent checks, paired learning/forgetting analysis, practice priorities, and assessment-growth proposals. |

PCC's coordinator uses the existing training service, operation journal,
executor, and worker lease. BW does not run a competing training scheduler,
and S³ does not gain execution authority by recommending a lesson.

A run advances through baseline evaluation, optional initial-parent evaluation,
lesson selection, native training, candidate evaluation, and a report. The
report selects a working parent for the next round. Working selection, private
preservation, and release/promotion are separate decisions.

Mutation requests carry stable operation IDs and exact request bindings. Run
revisions reject stale transitions. Retries retain the original request,
including its original revision; they cannot silently target a later round.
Native job identity is derived from the run, round, and registered policy.
The native request is saved before dispatch. Reconciliation reads that original
job rather than issuing another update under a new identity.

An interrupted evaluation can be recovered from its completed canonical evidence
when that evidence validates against the original model and runtime. Missing or
ambiguous original evidence requires operator review. This is bounded recovery,
not a claim of universal exactly-once execution across arbitrary crashes.

## PhD level: what the experiment can establish

There are three different questions: does the software execute its protocol,
does the model improve on the measured distribution, and does that improvement
generalize? Passing the first does not answer the other two.

For model learning, compare the original baseline, current working parent, and
candidate on identical identified cases under the same qualified runtime.
Retain paired outcomes: newly correct answers, previously correct answers lost,
and completion changes. An aggregate gain can conceal a regression; recording
that regression allows mixed review and repair in the next skill block. A
promising development candidate can remain useful while a stricter release
gate remains unmet.

Independent mastery, composition, and transfer/recovery are separate gates.
Difficulty also has separate axes: composition depth, dependence on distributed
context, environmental complexity, and autonomy. Passing advanced arithmetic
does not qualify a tool loop. Longer context does not itself demonstrate better
research. A world-interaction skill needs its environment and prerequisites
qualified before its score becomes meaningful.

S³'s new assessment-growth planner distinguishes three purposes:

| Purpose | Response to a perfect small panel |
| --- | --- |
| Machinery | Report integration success; infer no capability ceiling. |
| Fixed comparison | Keep the matching questions unchanged. |
| Adaptive learning | Propose more unseen cases at the same difficulty, then probes along one harder axis when declared coverage is met. |

The default adaptive coverage target is 96 cases per skill, divided into at
least 32 per gate. This is a policy setting, not a statistical proof of mastery.
Reliability depends on case diversity, sampling, dependence, grading, and the
target population. A perfect 4/4 panel is weak evidence about an unknown failure
rate.

An expanded assessment needs a new panel identity. Retain old anchors and
re-evaluate the original baseline, working parent, and candidate on the same
new panel. Comparing raw percentages across different panels confounds model
change with question difficulty. Keep new practice variations separate from
protected answers. Repeated development feedback still creates adaptive
selection pressure, so final qualification needs a separate sealed assessment.

The fixed optimizer study compares equal updates and ordered practice
presentations. Compute cost is a measured outcome rather than a stopping rule.
Hardware, runtime differences, and shared-GPU contention remain explicit;
wall-clock observations alone cannot establish optimizer efficiency.

## Applied summary: what to run and what to inspect

Start with software qualification on an authorized Linux host. From the S³
checkout, with the supported native CPU executable already built and NumPy
available for the generated fixture:

```bash
python -m sss machinery list
python -m sss machinery run learning-rounds-cpu \
  --pcc-root /owned/PCC \
  --bw-root /owned/BranchWrite \
  --executable /owned/cpu-build/pcc-native-train \
  --output /owned/new-learning-round-proof
```

Use a new output directory. Listing starts no model job. The selected suite
runs a generated tiny ordinary-Llama F32 model: three real CPU AdamW jobs,
16 updates each, with actual native forward logits and disjoint training and
evaluation prefixes. Its bounded classifier completion is not language-model
EOS behavior. The fixture exercises authenticated PCC HTTP and both real CLIs.
The [validation summary](../validation/learning-machinery-20261025-bb/README.md)
records its scope and recovery checks.

For an owner-configured service that has explicitly installed learning policies,
BW exposes the following controls. These examples run from the BW checkout:

```bash
python -m branchwrite learning --connection /owned/cow.json policies
python -m branchwrite learning --connection /owned/cow.json \
  start --operation-id lesson-run-001 --policy-id REGISTERED_POLICY_SHA
python -m branchwrite learning --connection /owned/cow.json status lesson-run-001
python -m branchwrite learning --connection /owned/cow.json \
  advance lesson-run-001 --operation-id lesson-run-001-step-001
```

Read status after each transition. It supplies `phase`, `revision`, and
`available_actions`. At lesson selection, `advance` takes admitted verified
lesson IDs. For training in progress, read the original job and use
`reconcile` only as indicated. Reuse the original operation ID and request
when recovering a lost acknowledgement. A deliberately new transition needs a
new operation ID. `round RUN_ID NUMBER` reads historical reports; `preserve`
requires an explicit name and notes and currently supports completed full
weights. It does not merge a LoRA adapter or publish weights.

PCC provides equivalent controls from its checkout through
`python -m tools.pcc_learning_loop --url http://HOST:8099 ...`, using its existing
request journal and `COW_API_KEY`. BW uses its configured connection and
`BW_COW_API_KEY`. Keep service credentials out of commands, reports, and Git.

After each round, inspect the exact model/job identity, case and runtime
identities, paired gains and losses against both baseline and parent, the next
working parent, and unresolved requirements. Preserve a named useful candidate
with its report; a private export is not broad acceptance or publication.

### Current limits and next integration work

The owner can now install registered actual-model policies through the optional
`learning_config` JSON setting. The [configured COW guide](CONFIGURED-COW-LEARNING.md)
explains exact model, context, case, runtime, practice and resource bindings.
The [two-round MiniCPM qualification](../validation/configured-cow-learning-20261025-bf/README.md)
measured **1/15 -> 5/15 -> 5/15** correct and **3/15 -> 9/15 -> 13/15** naturally
finished, with no baseline answer losses. These 15 cases qualify machinery;
they do not establish broad learning or a capability ceiling.

The assessment-growth module produces proposals. It does not yet generate new
questions, qualify their checkers, or execute a transition to a larger panel.
Learning rounds currently require explicit fresh optimizer-state recipes;
separately qualified exact optimizer continuation remains a different path.
Standalone LoRA merge acceptance and broad sealed real-model acceptance
remain open. No automatic model promotion is enabled.

See also [paired next-skill-block decisions](NEXT-SKILL-BLOCK.md),
[exact parent resolution](RESOLVED-LEARNING-PARENT.md),
[the actual-model LoRA mechanics probe](REGISTERED-LORA-MODEL-PROBE.md), and
[the fixed comparison and charts](COW-SHARED-ROOT-LEARNING.md).
