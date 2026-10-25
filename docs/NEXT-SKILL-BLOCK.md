# Recommend the next skill block

S³ can turn three completed evaluations into an offline recommendation: the
original baseline, the current working parent and a candidate. It reports gains
and losses, proposes fresh-practice focus groups and identifies which measured
candidate to retain as the next working parent. It does not train, execute tools,
allocate a GPU or promote a model.

```sh
python -m sss study next-block \
  --baseline /private/original/result.json \
  --parent /private/parent/result.json \
  --candidate /private/candidate/result.json \
  --output /private/new-proposal.json
```

All three inputs must contain complete outcomes on the same frozen evaluation
and numerical runtime. Their skill/gate assignments and case identities must
match. The output file must be new; an existing proposal is never overwritten.
The command emits a short summary and preserves its inputs byte-for-byte.

## What an operator receives

The recommendation separates three decisions:

- A working-parent choice: keep and advance, keep and repair, or retain the
  existing parent. This is an exploratory choice under the declared count-based
  policy, not a claim that every skill improved.
- Repair, review and forward-learning groups. Generate separately owned practice
  from those skill families; protected evaluation questions, answers and case IDs
  are absent from the proposal.
- The unchanged strict preservation gate. A promising working candidate can
  still be rejected for promotion because it lost earlier successes. Its
  evidence and useful learning are retained.

An operator must inspect domain changes, lesson provenance and resource admission
before creating the next PCC job. This command supplies no artifact paths or
execution authority. Resolve the selected identity against the existing PCC
candidate/evaluation receipts and verify the actual base, adapter and scale
before constructing a training request. [Owner-side identity resolution](RESOLVED-LEARNING-PARENT.md) now checks the
proposal against actual PCC artifacts. Durable multi-round execution remains
separate integration work.

## Version 2 identifies the entire candidate

The result has `schema: 2` and `kind: sss.next-skill-block.v2`. Its `baseline`,
`parent`, `candidate` and `next_parent` fields are explicit references:

```json
{
  "base_model_sha256": "<64 hex characters>",
  "binding_kind": "measured-composite",
  "candidate_model_contract_id": "<64 hex characters>",
  "candidate_adapters": [{"sha256": "<64 hex characters>", "scale": 1.0}]
}
```

A composite base-only evaluation has an empty adapter list. Older base-weight
evidence without a composite binding is labelled `base-weights-only`, retaining
only its measured base hash. Mixing bound and unbound evaluations is refused.
One composite identity cannot name conflicting base weights, adapters or scales.
Different outcomes attributed to an unchanged candidate are refused as a basis
for selecting a training parent. Investigate inference variation or provenance;
the separate paired-analysis API can still measure that variation.

Version 1 recommended `next_parent_sha256`. That field could not distinguish
two LoRA hats sharing one base model. Version 2 removes that ambiguous shorthand;
consumers must use the complete `next_parent` reference. Historical version-1
reports remain unchanged and must not be treated as adapter selection records.
The currently running GPU studies already continue their exact adapter and
optimizer artifacts independently of this planner.

## Actual evidence exercise

On the saved MiniCPM LoRA update-5 and update-6 development results, the command
returns `KEEP_AND_REPAIR`, selecting the actual update-6 adapter and scale.
Correct answers rise 282 to 298, with 24 gains and eight losses against the
immediate parent. Four of the original baseline's successes are lost. The
strict preservation gate remains `REJECTED`, and `promoted` remains false.

This exercise reanalyzes existing results; it makes no new inference or training
claims. Four corruptions of copied actual input evidence—conflicting contract,
partial identity, an injected adapter path and outcomes attributed to an unchanged hat—were refused without creating a
proposal. Original input files stayed unchanged. Forty-eight focused CPU checks
covered parent selection, composite identities, the actual CLI, shard merging,
curves and protected-practice guards.

[The recommendation and integrity observations](../validation/minicpm-native-learning-20261024/next-block-identity-at.json)
contain no protected question/answer text or model files.


## Later exercise: net gain can hide substantial churn

The same command on saved LoRA updates 14 and 15 recommends `KEEP_AND_REPAIR`
with update 15's exact base, adapter and scale. Correct answers rise 395 to 396,
but that one-answer net gain consists of 12 newly correct and 11 newly wrong
answers against the immediate parent. Natural finishes fall by one. Nine of the
original baseline successes are lost at both points; that unchanged count alone
would hide the newly learned answers that were forgotten.

The proposal identifies repair groups including signed-arithmetic transfer,
fraction transfer and place-value tasks. It keeps mixed review and forward
learning separate, without exporting protected questions or their answers.
The strict gate remains rejected and no model is promoted. This is an offline
exercise of existing evidence, not a curriculum change to the running fixed
68-update study. Resolve current artifact availability and actual PCC receipts
before executing any proposal; a saved reference is not proof a cached binary
still exists. [Owner-side resolution](RESOLVED-LEARNING-PARENT.md) is now supported; automatic
registration/import and durable multi-round coordination remain unfinished.

[The update-15 proposal](../validation/minicpm-native-learning-20261024/next-block-lora15-ax.json)
is available without protected task text. The [combined curve](COW-SHARED-ROOT-LEARNING.md)
shows the separate original-answer gain/loss series.
