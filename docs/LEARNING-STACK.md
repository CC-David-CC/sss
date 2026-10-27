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

## Fresh review practice with a fixed assessment

An owner can install fresh foundation practice without replacing the retention
panel. Replace only the review entry in `practice`:

```json
{
  "provider_id": "mixed-review",
  "role": "review",
  "kind": "foundation-practice-pack",
  "panel_id": "foundations",
  "configuration": "/owner/fresh-review.json"
}
```

`panel_id` names the existing `cow-foundations` assessment anchor.
`configuration` is a private owner file in the existing `CowLearningEvaluator`
format: a checked pack, rendered development definitions, model/tokenizer,
qualified execution profile and explicit execution limits. Its extra evaluator
validates and renders practice; it is not added to the assessment panels and its
development definitions do not replace the anchor's protected questions.

The fresh provider exposes only its checked practice lessons. It requires the
same immutable base, model contract, tokenizer, checker and renderer as the
anchor. It refuses practice exercise identities or exact prompt text reused
from the anchor's development or qualification partitions. This is an exact
overlap guard, not a semantic paraphrase detector. Owner configuration bytes,
practice membership and anchor bindings are rechecked before use.

Install a new configuration for a new curriculum. Changing the bytes of a
configuration used by an existing policy invalidates that policy; it does not
silently update an active learning run. BW verified target lessons and the
target/review batch minima continue to apply. PCC remains responsible for the
native training job, candidate and decision.

Use a Python environment containing both the declared BW tool dependencies and
PCC tokenizer dependencies for the joined installation. An inference-only
environment is insufficient for real BW lesson capture. The optional CPU
installation check uses actual BW tools and PCC lesson admission with a scripted
teacher; it explicitly prohibits model inference and native training.

The fresh-review path passed 17 controlled factory checks and the real joined
CPU installation check on source bytes matching the published Git content.
The [sanitized qualification receipt](results/independent-review-20261027/qualification.json)
records the source hashes, three unchanged assessment bindings and admission of
one verified BW lesson plus one fresh review lesson. It records zero model calls
and zero weight updates. These checks establish installation and lesson-admission
mechanics, not model learning or retention quality.

## Real 128-lesson preparation and HTTP admission

A later llm-60 installation used the retained working parent and kept all three
existing assessment bindings unchanged. It selected **124 fresh, independently
checked foundation examples and four verified BW action lessons**. The new
policy has a 128-lesson batch; the earlier 31-lesson policy correctly refused
that selection. The initial configuration-permission refusal was also preserved
and corrected before continuing. Neither refusal was treated as model failure.

The [installation receipt](results/independent-review-20261027/next-block-installation.json)
records the fixed assessment and exact selected-lesson digest. The subsequent
[HTTP admission receipt](results/independent-review-20261027/next-block-http-admission.json)
records all 128 lessons passing through the real **BW CowClient → PCC
LessonService** path. Stored lesson content matched the installed selection;
reusing the first operation ID returned its original receipt. A runner that
raises on native dispatch recorded zero calls. No learning run was created,
no inference occurred, and no weights changed.

This proves the larger lesson-selection and API-admission path, not improved
model behavior. Before training, install the frozen learning policy with the
actual native runner, preserve its source closure, and use a separate explicit
learning-run operation. The batch recipe and assessment identities belong to
that policy; do not change an active policy or reinterpret the old 31-lesson run.

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

A later [joined native round](JOINED-NATIVE-ROUND.md) completed all three
measurement panels, one counted update, the parent decision and private named
preservation. It lost 20 review passes overall; its working parent did not
advance. This supplies bounded integration evidence while repeatable operation,
tool-trajectory lessons and broader qualification remain unfinished.

## Division questions in new input packs

A later preparation using `without-replacement-v2`, seed 2026102603, was refused
before any model call: one division question repeated at two composition indices,
and another repeated at two transfer/recovery indices. The original refusal
and its seed are preserved; no automatic redraw or seed search was used.

New installations may explicitly choose `without-replacement-v3`. Division
operands now come from a finite Cartesian product under a coprime permutation.
All 384 supported gate/ordinal pairs use distinct nonzero operand pairs, and
practice, development and qualification operand domains remain separate.
Composition still requires nested arithmetic; reference answers are checked
independently. Nondivision questions retain v2 behavior. The global duplicate
guard remains active for every family; v3 does not promise that every other
randomly generated family is injective for every seed.

[The nine CPU checks](../validation/learning-program-20261024/division-unique-v3-20261026.json)
include the original v2 refusal, the same-seed v3 nine-skill panel with 864
questions, all 384 division ordinals in every split, independent answer checks,
source-pin tampering, finite bounds and preserved older pack identities.
This opt-in generator neither regenerates the fixed 68-update study nor changes
an already installed running policy. No model behavior or training is measured.

The optional division generator and the joined-report auditor are integrated in
this learning-stack branch. [Seventy-one CPU controls passed together](../validation/learning-program-20261024/joined-audit-v3-integration-20261026.json).
Existing frozen installations and the fixed 68-update study were not modified.

[Observed-memory placement](OBSERVED-MEMORY-PLACEMENT.md) uses matching PCC execution
observations to suggest useful GPU windows. PCC retains its existing leases and
allocation checks; forecasts add no workflow runtime or permission prompt.

The optional [BW action-practice export](BW-ACTION-PRACTICE.md) teaches recorded read/edit/check/finish turns through the real PCC append rules. CPU export and registry checks pass; native training on these longer contexts remains unqualified.


[Teach a different student from verified BW actions](BW-ACTION-TEACHER-TRANSFER.md) preserves the original source identity and explicitly declares teacher provenance. CPU export, audit and exact registry controls pass; actual student training and acceptance remain separate gates.
