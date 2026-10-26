# Install the complete learning assessment and practice policy

The existing PCC training configuration's `learning_config` can now name a
closed `sss.learning-stack.v1` installation. S³ constructs its real artifact
target, BW workflow, retention and approved-practice adapters, then returns the
existing `PanelLearningPolicy` interface to PCC. PCC still owns learning runs,
native training jobs, original worker leases and immutable candidates. This is
configuration of those components, not another workflow or training runtime.

This factory is an optional adapter. Core S³ still imports without BW, PCC,
NumPy, a GPU or a network. The currently qualified concrete evaluator family
is the existing dense MiniCPM/COW path; supporting a different native model
architecture still requires that architecture's PCC and renderer qualification.

## The installation

The owner installs private regular JSON files with mode `0600`. The factory
accepts known adapter kinds, roles and absolute configuration paths. Students
name the resulting installed policy and lesson IDs through PCC; they cannot
provide a checker module, script, executable, changed grant or approval flag.
Unknown fields/kinds and missing target, workflow or retention coverage fail
installation. Original file bytes and the actual loader source are bound into
the policy identity and checked again before use.

```json
{
  "schema": 1,
  "kind": "sss.learning-stack.v1",
  "panels": [
    {"panel_id": "repair", "role": "target", "kind": "cow-artifact", "configuration": "/owner/target.json"},
    {"panel_id": "tools", "role": "workflow", "kind": "bw-workflow", "configuration": "/owner/workflow.json"},
    {"panel_id": "foundations", "role": "retention", "kind": "cow-foundations", "configuration": "/owner/retention.json"}
  ],
  "practice": [
    {"provider_id": "verified-code", "role": "target", "kind": "bw-verified", "configuration": "/owner/approved-practice.json"},
    {"provider_id": "mixed-review", "role": "review", "kind": "foundation-practice", "panel_id": "foundations"}
  ],
  "practice_mix": {"minimum_target_lessons": 1, "minimum_review_lessons": 1},
  "policies": [
    {
      "title": "One complete mixed practice block",
      "training": {"mode": "full", "rank": 2, "steps": 1, "batch_size": 2, "learning_rate": 0.0001},
      "max_rounds": 2,
      "assessment_purpose": "machinery",
      "minimum_skill_cases": 3
    }
  ]
}
```

These are explicit small machinery limits, not quality defaults or a request
to approve a new trained model. Register an explicit fresh optimizer profile
with PCC and include its `optimizer_profile_id` in the recipe when required
by the runner. The optional full-mode rank field is retained by the existing
PCC request schema; it does not turn a full update into LoRA. Optimizer choice,
step count and native recipe validation remain PCC responsibilities.

Configure the three panels as described in [artifact assessment](ARTIFACT-ASSESSMENT.md),
[actual BW workflow assessment](WORKFLOW-ASSESSMENT.md), and the existing
`CowLearningEvaluator` foundation configuration. The latter binds the frozen
development file, independent checked practice pack, real renderer/tokenizer,
qualified COW profile/build and explicit GPU/context/output limits.
Approved BW registry entries use [verified-practice exports](BW-VERIFIED-PRACTICE.md).
All panels must bind the same immutable training base and model contract.

## What mixed practice means here

The foundation provider exposes only independently checked examples from the
practice partition of its installed pack. Development questions remain
assessment-only. The BW provider exposes only its exact owner-installed exports.
The factory rejects an exact protected assessment baseline reused as practice,
even with different hidden oracle rows or a renamed case.

Every selected block must meet the explicit target/review minima. Every selected
lesson must also fit in the native batch; listing review examples outside that
batch cannot satisfy the mix check. This constrains example membership, not
equal loss mass: examples have different token lengths. Inspect actual native
presentation counts and loss masks before claiming balanced gradient influence.
An explicit zero review minimum permits a single-example machinery policy;
it must not be presented as a retention-qualified quality policy.

The three measurements remain distinct. BW may finish an attempt with a wrong
program; the target oracle can reject that program. Retention can regress even
when aggregate learning improves. Per-panel reports preserve those outcomes.
`machinery` coverage is not a model-capability acceptance claim. The existing
working-parent decision and strict qualification remain separate, and the
student cannot promote its own candidate.

## API and inference source identities

The owner-side PCC API and the qualified inference execution checkout may be
different source trees. Their profile binder implementation must match exactly.
The evaluator pins the actual API/native-training and renderer/tokenizer source
files used by the owner process, while the child verifies its original complete
execution-source closure and native build. This records both identities instead
of pretending an older inference package is the current training API. A source
or input change creates a new policy/baseline; old evidence keeps its original
identity. No fresh-oracle fallback or implicit numerical-profile change occurs.

## Validation and current limit

Sixty-four CPU unit/control checks passed, including closed kinds/roles,
complete measurement coverage, exact target/review membership, batch capacity,
protected-source overlap, changed owner files, duplicate JSON fields, links and
registry validation. A separate installation control then used actual model
metadata/template/tokenization, actual BW tools with scripted synthetic teacher
proposals, isolated independent source checks, the concrete three panel bindings
and the real PCC public lesson-admission API. It admitted one checked code lesson
and one review lesson while a runner guard prohibited all native training.

The first installation attempt correctly refused an old synthetic fixture whose
source overlapped a protected assessment. That refused attempt remains private
engineering evidence. A fresh owned input from a different bug family passed;
the protected task was not relabelled as practice. No protected question or
answer was exported to training. Teacher proposals were scripted, not generated
by the tested model.

The installation control performed no real panel scoring, inference, training
or acceptance decision. Its roughly four-minute wall time includes repeated
full-model hashing and proof replay; it is not inference throughput. A genuine
joined native train/test/decision/preserve round is the next required evidence.
The complete reusable learning loop is not yet qualified by this installation.

```sh
python -B -m unittest -v sss_tests.test_learning_stack \
  sss_tests.test_verified_practice_registry sss_tests.test_learning_panels \
  sss_tests.test_cow_learning sss_tests.test_artifact_assessment
```

The optional `sss_integration.test_learning_stack_cpu` requires explicit owner
model/profile/execution/build/BW paths and the real PCC implementation fixtures.
Its output is private and its runner deliberately refuses training. Keep raw
lesson/case/capture files outside Git; publish sanitized source/evidence receipts.

## Generating a fresh review panel

The first joined native-round launch was refused before any model call or update:
`without-replacement-v1` produced the same fraction question at development
composition indices 0 and 31 for seed 2026102601. The duplicate guard was correct.
The original attempted inputs and refusal remain private, unchanged.

For new packs, `without-replacement-v2` adds a fraction operand permutation with
no replacement, retries, seed search, or filtering by answers. Its composition
questions require evaluating a nested division/multiplication expression. Both
operand magnitudes and question text remain separated across practice,
development and qualification. Other families retain v1 generation and the
pack-wide duplicate check still refuses any collision: this is not a claim that
every implemented family has an injective generator for every possible seed.

The new pack records both generator source hashes. Existing legacy/v1 packs and
the fixed 68-update comparison are not migrated or regenerated. Eleven CPU
checks passed, including the original refusal, the exact nine-skill/864-question
new development panel, split separation, reference correctness, finite bounds,
legacy pack identity and tampered source rejection. No model learning result
follows from these generator checks.

## Split API and native-execution installations

When the PCC API and the qualified native worker use separate source trees,
children must import the same API/rendering files as their parent and the
qualified experimental backend from the execution tree. The child environment
now preserves both roots. Artifact and BW workflow children also require the
parent evaluator identity before reading candidate inputs or entering GPU work.
A mismatch is an installation failure, not a model failure or an excuse to relax
the evidence comparison.

The first joined baseline completed two artifact cases (one correct, both
naturally finished), but its parent rejected their different child evaluator
identity. Those raw outcomes remain private diagnostics. They are not an
accepted joined baseline, and no training update had occurred. The corrected
joined run uses fresh protected visible bug variants; completed questions are
not redispatched. The fixed 68-update study remains separate and unchanged.

The correction passed 33 CPU/control checks. On llm-60, actual artifact and
workflow parent/child constructions then produced identical evaluator identities
using the separate API and qualified-execution installations, with zero model
calls. This preflight proves installation equivalence, not a completed native
learning round. See the [sanitized receipt](../validation/learning-program-20261024/child-installation-20261026.json).

A subsequent independent native mixed block executed and preserved its diagnostic
GGUF. See [the measured result and unresolved joined assessment](NATIVE-MIXED-BLOCK.md).
The native job is complete; the full reusable learning loop is still unqualified.
