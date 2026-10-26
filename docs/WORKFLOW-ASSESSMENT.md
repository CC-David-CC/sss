# Assess the workflow as well as the answer

`sss.adapters.workflow_evaluation.BWWorkflowEvaluator` measures actual model-driven
BW work through a native PCC/COW server. It complements the
[artifact-only target panel](ARTIFACT-ASSESSMENT.md). The distinction matters:
generating a correct source file does not prove that a model can inspect a
project, save a repair, check it, and explicitly finish.

S³ owns the frozen development cases and the independent grade. BW owns the
task interpreter, grants, file tools, isolated commands, ledger and archival
capture. PCC owns model/profile identities, GPU admission, context, grammars
and consumed native model requests. This adapter adds no workflow runtime,
sampler, stateless-chat substitute or training engine.

## What a workflow pass requires

Each original case includes source bytes/mode, skill and mastery gate, plus a
fixed isolated affine/clamp/fold oracle. Hidden oracle rows are not supplied to
the model. Each attempt receives a fresh owned project with `task.py` and an
input file it must preserve. BW runs with its existing project-file grants,
direct tool grammar, greedy decoding, thinking disabled and explicit limits.

The evaluator requires archived evidence of all of the following:

1. Read `task.py`, then edit that file.
2. Run a successful check whose recorded inventory matches the captured files.
3. Explicitly finish after that check, with BW's recorded workflow verification.
4. Preserve the other input file and both original file modes.
5. Pass the independently executed hidden oracle on the actual saved program.

`finished` measures the first four requirements. `passed` additionally requires
the independent oracle. A model can finish a workflow whose program is wrong.
Natural EOS alone is neither workflow completion nor program correctness.
All model generations and tool effects must have supported, settled original
BW/COW receipts. A partial or unsupported attempt is unavailable, not a zero
that can silently enter a learning/forgetting report.

BW now provides `capture_assessment(state, output)` and:

```sh
branchwrite lesson capture-assessment /owner/run --output /owner/new-archive
branchwrite lesson capture-show /owner/new-archive --expected-capture-id HASH
```

An assessment archive has no failure link and grants no training approval. It
can describe an unfinished attempt or a verified workflow without claiming to
be a correction. Existing failure/correction capture rules are unchanged.
Archives replay copied ledger, native journal, exact file bytes and modes;
they do not call the model, execute a command or contact a retired server.

## Owner installation

Use the matching installed BW assessment API and a source-qualified dense PCC
runtime. Configure an **unattached** base COW profile; candidates bind through
the existing full-weight/LoRA PCC profile helpers. The new workflow panel's
attached-LoRA execution still requires its own qualification.

The closed owner configuration contains the artifact evaluator fields plus
`maximum_steps` and `maximum_requests`:

```json
{
  "schema": 1,
  "pcc_root": "/owner/qualified-pcc",
  "bw_root": "/owner/qualified-bw",
  "cow_profile": "/owner/unattached-base-profile.json",
  "runtime_proof": "/owner/existing-native-build-proof.json",
  "cases": "/owner/protected-workflow-cases.json",
  "gpu_index": 0,
  "gpu_uuid": "GPU-OWNER-OBSERVATION",
  "maximum_tokens": 256,
  "maximum_steps": 512,
  "maximum_requests": 8,
  "minimum_free_mib": 20000,
  "maximum_initial_utilization": 100,
  "timeout_seconds": 900
}
```

Values above illustrate an explicit small probe, not universal hardware or
quality defaults. Context capacity, prefill size, numerical operators and EOS
IDs come from the pinned profile. `maximum_tokens` limits a native request;
`maximum_requests` limits each BW model action, **not the whole task**. The
interpreter step bound and owner child timeout also apply. Record actual use
before comparing harness efficiency. An operator timeout or unresolved request
holds the assessment; it is not evidence of incorrect reasoning.

The adapter uses the existing parent worker file descriptor, process identity,
immutable dispatch intent and recovery method. Install it as the `workflow`
role of `LearningPanelEvaluator`, with separate real `target` and `retention`
panels and independently approved practice providers. Cases are development
assessment inputs; they must never be exported as practice lessons. The
owner-configured [learning-stack factory](LEARNING-STACK.md) is implemented and installation-tested. A genuine joined native learning round remains unqualified. This panel alone does not establish the entire loop.

## Evidence and recovery

The child starts the existing PCC HTTP components under the same GPU lease
used by direct COW evaluation. BW uses that real service and its own interpreter.
The service is retired before a complete panel settlement is written. Exceptional
exit also records retirement after handlers, model and grammar resources close.
The original failed/partial world is retained for inspection.

`recover(candidate, directory)` validates an already complete original result
after its exact worker is gone. It replays the assessment archive and the saved
independent oracle evidence. It never resumes an unstarted case, retries a model
request, changes a decoder profile or reruns an effect. Missing, live or partial
original evidence remains a hold requiring explicit owner recovery. A child
failure cannot be replaced by a copied passing summary.

Source and input hashes bind the panel, BW implementation and instruction assets,
native build and profile. A source/profile change requires a new policy and
baseline. Keep the original source revision when inspecting older evidence.

## Machinery validation

The scripted CPU checks use actual BW tools, COW grammar/HTTP handling and the
isolated OS command boundary. They distinguish incomplete and finished attempts,
reject invented correction links, replay after original project retirement,
and verify exceptional HTTP/model/lease teardown. They do not demonstrate model
learning. Existing capture and panel-composition controls remain applicable.

```sh
python -B -m unittest -v tests.test_assessment_capture tests.test_lesson_capture
python -B -m unittest -v sss_integration.test_workflow_assessment
```

These optional tests need the matching BW/PCC sources and PCC's implementation
test fixtures on `PYTHONPATH`, plus the pinned tokenizer/grammar/OS dependencies
from [verified practice](BW-VERIFIED-PRACTICE.md). Core S³ remains importable
without those dependencies. Native probe results are recorded separately; a
single workflow is an integration observation, not a capability estimate.

## First native observations

The [sanitized evidence receipt](../validation/learning-program-20261024/workflow-panel-native-20261026.json)
records the actual model, source, runtime and original-result hashes. The first
8k attempt exhausted context and retained an unresolved request. It remains
unscored and was not replayed. A distinct protected case was then admitted with
an explicit 32k profile, within the model file's recorded 128k native limit,
without position scaling. These are different cases/configurations, not a paired
claim that more context fixed the earlier attempt.

On the 32k case the real model completed read, edit, current passing check and
finish, preserving the input. Its actual saved program retained the sign error
and failed the independently executed oracle. Result: **1 workflow finished,
0 correct artifacts out of 1**. That is useful integration evidence: BW's own
passing check did not become an independent correctness claim. It is not a
capability estimate, learning gain or optimizer comparison. No weights changed.
The existing full FP32 checkpoint was used as the base; attached LoRA and a
new full-weight training candidate have not been qualified by this panel.

Sixty-seven distinct checks passed with no skips: 34 pure artifact/composition,
18 existing capture, one assessment capture, two scripted workflow/lifecycle,
nine dispatch/recovery, and three actual-native read-only recovery controls.
The replay controls refused a consistent summary/count rewrite and a changed
tool observation without new inference or independent oracle execution.
Repeated full-model hashing still adds validation cost; the 95.54-second native
probe wall time and 76.64-second replay suite are not inference-only timings.
