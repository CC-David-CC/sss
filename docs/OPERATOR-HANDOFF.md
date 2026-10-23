# Operator handoff for a smaller exploration model

Read this first, then START-HERE.md. Your job is to run a bounded declared
experiment, preserve its evidence, interpret the checks and propose the next
experiment. S³ owns assessment. BW owns actual task/tool execution and its
ledger. PCC owns model state, resources and weight candidates. Do not implement
a second tool/workflow runtime in this project.

## Establish the starting point

1. Read AGENTS.md and the private human handoff for machine permission and exact
   checkouts. Git availability is not permission to use a machine or GPU.
2. Record `git status --short`, `git rev-parse HEAD` and
   `python -m sss explore doctor`. Preserve any existing changes and results.
3. Run the reference walkthrough in START-HERE.md in a new private directory.
   Inspect both its all-correct answers and its deliberately false qualification.
4. Inspect the chosen skill JSON, prerequisites and coverage note. Use an
   implemented bounded family. Planned nodes and unsupported difficulty cells
   cannot be scored as passes. Above-prerequisite probes are diagnostics only.

## The normal exploration cycle

- State one question, the skill IDs, profile, four difficulty coordinates, exact
  metric, comparison/control, budget and what would falsify the hypothesis.
- Start with a small probe. Freeze it before the first endpoint request. Keep
  model revision, tokenizer, template, harness revision, thinking, tool mode and
  retrieval mode explicit. Compare modes in separate runs.
- Confirm the human authorized that endpoint/resource window. A running service
  or an empty-looking GPU is not authorization. Do not stop someone else's job.
- Run `explore run` once against the original frozen directory. Inspect the
  assessment and original private outputs. Never substitute a model's claim of
  success for an independent result or actual filesystem/process evidence.
- Report the count and denominator, gate, difficulty cell, profile, infra errors
  and limits. A probe can locate weaknesses; it cannot qualify a skill.
- Propose one-axis changes. Keep prior successes in a frozen protected retention
  pack. Practice uses separately generated owned families; qualification answers
  and protected diagnostic traces must not become training examples.

There is no automatic training or promotion in these exploration commands.
PCC schema-2 lessons can select verified thinking + actions + answers, or actions
+ answers only. Inference thinking is a separate setting. Turning off thought
labels does not detach the context's gradients. Do not invent verification for
thoughts, replace a failed answer, or call a generated demonstration a model run.

## Stop and preserve evidence

| Observation | Required action |
| --- | --- |
| Existing output directory or outcomes | Inspect it. Do not delete it and repeat an uncertain run. |
| Changed source/catalog/profile identity | Restore the inspected version or declare a new experiment. Never mix results. |
| Timeout, refused admission, parser/backend error | Record unavailable infrastructure evidence. Do not count it as a correct answer or a model skill failure. |
| Candidate fails a protected earlier success | No qualification/promotion; preserve regression and original evidence. |
| Missing checker, unsupported cell or unready environment | Stop that branch. Report the missing machinery. |
| Memory estimate, gradient or reload mismatch | Stop native training tests and hand the evidence to an engine maintainer. Do not raise limits or relax tolerances. |
| Unclear machine permission or another job on the GPU | Ask the human before any access/allocation. Leave other jobs alone. |

Do not change scoring thresholds, patch the reference to match the model, or
reinterpret ambiguous outputs until they pass. Changing an evaluator is separate
engineering work with a distinguishing test and a new evidence identity.

## Reproducible CPU mechanics recipes

Core: `python -m unittest discover -s sss_tests -v`.

Real Linux code fixtures, in prepared disposable bubblewrap namespaces:

```sh
python -m sss_integration.foundation_linux --output /your/private/new-linux-proof
python -m sss_integration.external_apps_cpu --output /your/private/new-app-proof --apps /your/owned/pinned-app-install
python -m sss_integration.research_archive --output /your/private/new-archive
```

Check `--help` before running a recipe. The external applications are pinned in
the validation record. Their deterministic endpoint is a protocol fixture;
`model_inference=false` must remain visible. The archive uses a reference UTF-8
byte tokenizer, not Wen's tokenizer. Its generated experiments measure comparison
counts including setup cost, not wall-clock algorithm speed. The timed lane
fixture is synthetic; the harness prepares it and measures timing separately
from collision-free actions. No physical vehicle or game competence is implied.

Native CPU lesson wiring, with separately inspected PCC/BW checkouts and build:

```sh
python -m sss_integration.lesson_native_cpu --pcc-root /owned/PCC --bw-root /owned/BW --native-executable /owned/build/pcc-native-train --workdir /your/private/new-native-proof
```

This generates a tiny random hybrid model. It must never point at Wen weights.
Long-context native proofs use PCC's explicit `tiny-cpu-long-v1` profile: bounded
tiny CPU geometry, 32K maximum, at most 256 selected targets, ordinary full-graph
backprop. The other tokens still supply differentiable context. This is not an
approval for long-sequence Wen training, CUDA long training, section-adjoint
training, or widening the normal 8K admission limit.

## What the next operator must leave

Save the exact commit/source hashes, commands, private output locations, original
failures, independent verification, model/endpoint identities, resource use and
settlement, and a plain-language conclusion. Include the next concrete experiment
and unresolved question. Update the human-readable handoff before changing
machines or ending the session. Never put credentials or protected test material
in the public handoff. Keep original archives; working summaries are disposable.

## Existing BW domains

See [Blender, build123d and other BW workflow recipes](BW-WORKFLOWS.md) and
`python -m sss workflows list`. Existing execution and version-scoped evidence
are mapped to S3 prerequisites. The operator prepares domain environments;
new per-cell model qualifications remain separate.

Training admission follow-up: The retention guard now inspects admitted tokens across complete multi-turn lessons. Protected validation or blind prompts embedded behind role prefixes or in completions are refused. Four distinguishing unit checks and the actual four-run native CPU guard integration passed.
