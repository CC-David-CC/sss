# Real model-generated artifact assessment through PCC/COW

S³ now has a concrete artifact assessment panel for the learning-policy
composition. A model repairs a saved Python artifact, and S³ independently checks
the generated program through BW's actual isolated command boundary. Producing
valid JSON and stopping naturally are measured separately from program correctness.

The first qualified GPU probe used an existing FP32 standard-Muon update-42
MiniCPM5-2B checkpoint on llm-49. It answered two distinct repair questions with
canonical artifact JSON and native EOS. One program passed the independent
checker; the other retained the original arithmetic bug. Both oracle processes
exited successfully and their original source files remained unchanged.

This is **two real model questions**, not a capability estimate, optimizer ranking
or evidence that new training occurred. The purpose is to exercise an actual
target measurement in the reusable loop. The separate frozen 68-update experiment
and its questions were unchanged. The probe's weights were unchanged.

## Ownership and execution

`sss.artifact_assessment.ArtifactAssessmentCase` is an immutable development
assessment definition. Its private descriptor binds a fixed affine/clamp/fold
checker, original artifact bytes and mode, skill ID and mastery gate. Hidden
checker inputs and expected results do not enter the model prompt. Two cases with
identical visible tasks cannot be counted as independent questions merely by
changing hidden inputs. These assessment descriptors are never practice approval.

`sss.adapters.artifact_evaluation.CowArtifactEvaluator` extends the existing
`CowLearningEvaluator` dispatch and recovery path. PCC owns profile binding,
GPU admission, native model loading, shared-prefix requests, stopping and process
receipts. S³ supplies the task and scoring contract. BW's existing fixed isolated
oracle runs the exact generated `task.py`; no model-generated command or checker
is executed. An unavailable checker holds the assessment instead of becoming a
model failure or pass.

Every result retains the actual base/adapter identity, frozen case and runtime
identities, original tokens/decoding/EOS, raw oracle evidence and complete settlement.
Validation rereads the original evidence, not just the aggregate score. Recovery
requires the original evaluator child to be gone and rebuilds no model output.
The focused replay checks inject reader faults without modifying the actual
saved evidence or making another model/oracle call.

## Install the owner configuration

Use the matching qualified PCC source tree, native bridge build proof and an
unattached dense COW base profile. The parent and execution child must use the
identical PCC profile-binding implementation. A parent service and inference
child can use different PCC checkouts only when those binding bytes match and
the execution child's complete selected source closure matches its own profile.
Do not rewrite expected hashes to admit a changed runtime.

The private owner configuration has exactly these fields:

```json
{
  "schema": 1,
  "pcc_root": "/owner/qualified-pcc",
  "bw_root": "/owner/branchwrite",
  "cow_profile": "/owner/base-profile.json",
  "runtime_proof": "/owner/qualified-native-build.json",
  "cases": "/owner/protected-artifact-cases.json",
  "gpu_index": 0,
  "gpu_uuid": "GPU-physical-identity",
  "maximum_tokens": 256,
  "minimum_free_mib": 12288,
  "maximum_initial_utilization": 100,
  "timeout_seconds": 900
}
```

GPU identity and headroom must describe the actual authorized hardware. The probe
used a separately derived 1,024-token inference profile with 512-token prefill
batches. Its two input lengths were 424 and 447 tokens, each with the full
256-token output allowance. This did not relax PCC's separate 512-token dense
training qualification or establish long-context inference correctness.

Install genuinely separate development cases using
`ArtifactAssessmentCase(...).descriptor()` and write the resulting list to the
private case file. Practice cases and expected answers stay outside this panel;
approving and admitting a lesson requires the separate verified practice path.

```python
from sss.adapters.artifact_evaluation import CowArtifactEvaluator

target = CowArtifactEvaluator(absolute_owner_configuration)
target.binding()  # Pin into the owner-installed learning policy.
```

Use this object as the target panel in
[`LearningPanelEvaluator`](BW-VERIFIED-PRACTICE.md#join-target-workflow-and-retention-measurements-in-a-pcc-policy).
PCC's ordinary learning-run worker supplies the fresh backend directory and
its existing worker lease. It supplies `None` for the initial base evaluation,
or its immutable full/LoRA candidate record. The evaluator binds that exact
candidate to the existing native COW profile; it cannot update or promote it.
The initial native qualification used the existing full FP32 checkpoint as the
base. Artifact evaluation with an attached LoRA has not yet been exercised by
this new panel; inherited binder support is not a new qualification result.

The child module `sss_integration.artifact_evaluate` is the adapter's existing
process boundary. Users of the learning API do not supply its paths, process
arguments, scores or evaluator implementations. An HTTP/student request names
the installed policy and admitted lesson IDs only.

## Verification and limits

The pure core and existing composition tests passed 34 methods. The existing
COW dispatch/recovery controls passed nine methods after extracting a small
environment hook; its default execution behavior is unchanged. Four optional
read-only replay tests then recovered the actual native probe and refused altered
sampled tokens, a score/count rewrite, and a changed saved oracle verdict. No
new model or oracle execution occurred during replay.

```sh
python -B -m unittest -v sss_tests.test_artifact_assessment \
  sss_tests.test_learning_panels sss_tests.test_cow_learning

SSS_ARTIFACT_NATIVE_PROBE=/owner/evidence/completed-probe \
  python -B -m unittest -v sss_integration.test_artifact_evaluation
```

The optional environment needs the actual matching PCC and BW checkouts on
`PYTHONPATH`, PCC's branching-context source path, and the installed tokenizer
and BW dependencies described in the verified-practice guide. Original protected
questions, responses, source programs, oracle inputs and filesystem paths remain
private. The [sanitized qualification receipt](../validation/learning-program-20261024/artifact-panel-native-20261026.json)
records exact source and original-evidence hashes and the bounded results.

Validation currently rechecks full model hashes repeatedly. The 68.38-second
probe wall time includes real inference, independent checks, and multiple complete
validation/recovery passes; it is not an inference-throughput measurement. Avoid
claiming the earlier COW forward-probe speedup for this whole path.

This concrete target panel is one required part of the production loop. The [actual BW workflow panel](WORKFLOW-ASSESSMENT.md) now has an implementation and
scripted machinery checks; its native evidence is reported separately. Joined
retention/practice configuration, partial assessment continuation and a complete
real-model train/test/acceptance round still require integration and qualification. A target artifact pass does not prove
that BW chose and verified the right tool actions or that a model retained its
other skills. The learning loop remains in development.
