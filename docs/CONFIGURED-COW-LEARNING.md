# Configure an actual-model COW learning loop

The opt-in owner configuration now constructs a complete S3 learning policy over
PCC's existing native trainer and shared-prefix COW evaluator. A person or agent
can drive it with the same BW/COW commands described in
[Learning machinery](LEARNING-MACHINERY.md). It adds no workflow runtime or
sampler. The [actual MiniCPM qualification](../validation/configured-cow-learning-20261025-bf/README.md)
completed two rounds; it is a machinery check, not broad acceptance.

## Ownership and prerequisites

S3 supplies exercises, exact checkers, independent practice, paired learning and
forgetting analysis and assessment proposals. PCC owns native execution, model
and adapter identities, leases, durable rounds and candidates. BW is a client
of the existing service and retains its task/request journal.

Use matching reviewed PCC/S3 source revisions, a supported native executable,
a qualified unattached dense COW base profile, its exact source closure, the
qualified bridge/oracle proof, the exact base GGUF and its actual tokenizer.
The owner supplies physical GPU UUID, context and memory bounds, fresh-state
optimizer profiles and admitted resources. Clients cannot select filesystem
paths or checker code. A changed source closure needs explicit qualification;
do not edit hashes merely to make a validator stop refusing it.

## Prepare independent practice and protected checks

The existing preparation command performs no model updates:

```bash
python -m sss_integration.optimizer_study_prepare \
  --pcc-root /owned/PCC --model /owned/base.gguf \
  --model-contract-id ACTUAL_BASE_CONTRACT_SHA \
  --output /private/new-practice --seed 0 \
  --skills math.add.carry math.subtract.borrow \
  --practice-per-gate 2 --checks-per-gate 1
```

This is the small qualification size. Curriculum prerequisites can add skills;
inspect `preparation-result.json` for actual coverage and token maxima. The
without-replacement generator separates practice, development and qualification.
Keep protected records private. For an adaptive capability panel, choose enough
varied checks for the declared coverage target (default 96 per skill, 32 per gate).
Do not expand the frozen68 comparison. The preparation artifact's legacy
optimizer-study label does not impose a fixed training-time comparison.

Only submit admitted checked practice lessons from the preparation service's
`lesson-service/lessons` records to the new training service, using the normal
lesson endpoint/client. The evaluator reconstructs every allowed lesson from the
independent reference, checker and actual renderer. A client attestation alone
cannot insert a different answer into this policy's practice set. Lesson choices
can use measured failure groups plus mixed review; protected answers are never
copied into practice.

## Owner learning JSON

Add `learning_config` with the absolute path of a private JSON file to the
existing PCC training configuration. It is mutually exclusive with the legacy
`skill_guard_config`. Keep the existing `runner` and its admitted optimizer
registry. A registry contains 1-8 explicit policies:

```json
{
  "schema": 1,
  "evaluator": {
    "pcc_root": "/owned/PCC",
    "cow_profile": "/private/qualified-unattached-base-profile.json",
    "cases": "/private/new-practice/development-private.json",
    "evaluation_id": "ACTUAL_EVALUATION_SHA_FROM_CASE_FILE",
    "practice_pack": "/private/new-practice/pack-private.json",
    "oracle": "/owned/qualified-build/llama-dense-fresh-oracle",
    "runtime_proof": "/private/qualified-build.json",
    "gpu_index": 0,
    "gpu_uuid": "GPU-ACTUAL-PHYSICAL-UUID",
    "context_tokens": 512,
    "batch_tokens": 512,
    "maximum_tokens": 64,
    "stop_token_ids": [1, 130073],
    "minimum_free_mib": 24576,
    "maximum_initial_utilization": 50,
    "timeout_seconds": 900
  },
  "policies": [{
    "title": "Owner MiniCPM learning machinery check",
    "training": {
      "mode": "lora", "rank": 16, "batch_size": 3, "steps": 1,
      "learning_rate": 0.0001,
      "optimizer_profile_id": "ACTUAL_REGISTERED_FRESH_STATE_PROFILE_SHA"
    },
    "max_rounds": 2,
    "assessment_purpose": "machinery",
    "minimum_skill_cases": 96
  }]
}
```

Placeholders deliberately fail validation. The stop IDs shown are MiniCPM's
qualified configuration; another model requires its own tokenizer, rendering,
stopping and native support checks. The JSON file is owner configuration, not a
portable promise that the same settings fit every GPU. The trainer and evaluator
share existing account leases; no other serving process is automatically evicted.

`machinery` does not infer capability ceilings. `adaptive_learning` enables
assessment-growth recommendations. Fixed comparisons are refused by this
adaptive registry. A larger context is accepted only within configured bounds;
the actual test above qualifies 512 tokens, not 128k research stories.

## Drive, inspect and recover

Start the normally configured authenticated PCC service, list policies through
BW or COW, and use the returned registered ID. Read status and `available_actions`
after each transition. Use exact revisions and stable operation IDs. At lesson
selection choose admitted lesson IDs; after training reconcile its original job.
Read `round RUN NUMBER` to inspect both baseline and immediate-parent gains,
losses and completion changes. Continue a working parent only as the report and
owner policy allow. A working selection is separate from sealed release approval.

Evaluation invokes the existing shared-prefix COW path in an isolated child,
with the original worker lease inherited. Source/input/model/hat/runtime/checker
bindings are frozen before dispatch. Raw token receipts, exact decoding, EOS
stopping and independent grades must agree with the complete original result.

A surviving original evaluator blocks redispatch. A failed child, incomplete
settlement or changed evidence requires operator review. A lost parent exit
receipt can be reconciled only from complete validated original evidence after
the child is gone. Recovery issues no fresh model evaluation or training call.
This does not promise universal exactly-once execution after arbitrary failures.

Current rounds deliberately start fresh optimizer state while continuing the
selected weights/adapter. Exact moment continuation is a separate qualified
path. Automatic panel generation/transitions, sealed broad acceptance,
standalone LoRA merge acceptance and named merged-GGUF preservation remain
incomplete. Preserve useful private candidates and their evidence; do not call
this path an automatically improving or automatically promoted model.

## Audit an already completed run

Use the supported [original-evidence audit](COW-LEARNING-AUDIT.md) after a round
settles and before retiring required artifacts. It checks the saved chain without
starting inference or training. Queued/running or ambiguous work is refused.
