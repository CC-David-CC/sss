# Foundation training pilot

S³ can now prepare a bounded active training pack from the progressive graph and
pass it to PCC's existing lesson service and skill guard. This is an operator API.
The guided exploration CLI remains an evaluation interface; the older configured
training adapter still covers its five legacy arithmetic skills. Do not pass this
new pack to that older adapter or assume its fixed token and GPU policy applies.

The graph stays authoritative. The active guard's single-parent grouping is only
a training/reporting view; `requires` and `graph_id` retain the actual prerequisite
edges. This view does not grant skill mastery or environment permissions.

## Prepare owned practice

```python
from sss.adapters.foundation_training import build_pack, initialize
from sss.adapters.pcc_foundation_render import PCCFoundationRenderer

pack = build_pack(
    ["math.add.carry", "math.fraction.add", "state.registers"],
    seed=20261023, practice_per_gate=4, checks_per_gate=2,
)
renderer = PCCFoundationRenderer(actual_pcc_text_components)
tree = initialize(
    actual_pcc_lesson_service, pack, renderer,
    renderer_sha256=renderer.renderer_sha256,
    tokenizer_sha256=actual_tokenizer_metadata_digest,
)
```

The two `actual_...` objects come from the owner's configured PCC model and
lesson service. This code does not create a server, select a GPU, train a model,
or replace the host's resource checks. Use PCC's schema-2 rendered tokenizer
callback with `parse_special=True`, as its current `configured_service` does.

This example includes nine skills after adding prerequisites. It records 108
practice occurrences, 54 development checks and 54 blind checks. One practice
question repeats across generated occurrences; the manifest reports this as
rehearsal, not 108 independent questions. Evaluation duplicates or cross-split
overlap are rejected without redrawing. There are three exercise gates for each
skill: independent, composition and transfer/recovery.

All practice answers come from the owned reference generator and pass the
independent checker. No observed evaluation answer is copied into training.
The initializer renders and admits every lesson before recording any lesson.
An overlong lesson fails admission; it is never truncated or silently omitted.

Under the private PCC lesson store, `foundation-pack-<id>/` keeps the frozen
manifest, independent practice evidence, the active tree, admission receipt and
`finished-training-examples.txt`. The text file contains practice question/answer
pairs only. Keep the manifest and held-out questions outside public Git.

## Connect the existing guard

`FoundationGuardEvaluator` accepts the frozen pack, active tree and a host-owned
session factory. It then fits the existing `SkillGuardRunner`; no second workflow
runtime is introduced. Its constructor also pins the base model hash and the
inference runtime identity.

The factory's interface is:

```python
with session(candidate, private_output_directory, inherited_worker_fd) as (model, receipt):
    # model uses the existing S³ OpenAIModel callback interface.
    # receipt has exactly base_sha256, adapter_sha256 and runtime_id.
    ...
```

The host must actually start or select that candidate using PCC's pinned profile,
enforce the declared resource/output/time budgets, preserve raw responses, and
settle its owned process and GPU leases on exit. Merely labeling an endpoint with
a candidate name is insufficient. Candidate file hashes and session receipts are
checked before any evaluation request. A transport error stops the evaluation;
it is not converted to a model failure or retried as a new request.

The existing guard interleaves every active skill with focused practice and
protects previously passing checks. Set the round size and focus fraction so each
skill has enough distinct lesson records for the requested share. Blind checks
remain separate. A pilot's `qualified` flag is local to that frozen training
policy, not the formal 256-trial-per-gate mastery qualification. This pack also
does not establish preservation of tools, coding, writing or other omitted skills.

This initializer supplies checked final answers and template terminators. It does
not generate or certify thinking text. PCC's separate verified-thinking and
answer/action-only target policies remain available for curricula with checked
reasoning spans. Do not train truncated reasoning from a failed assessment.

## What was exercised on 2026-10-23

- Six distinguishing adapter tests passed, including changed splits/checkers,
  leaked questions, overlong lessons and an incorrectly selected candidate.
- All 108 lessons passed Wen 1.1's actual tokenizer and serving-template checks.
  They span 58–375 consumed training tokens. This establishes token admission,
  not GPU training capacity.
- The pack fed the real PCC native CPU trainer through the existing guard:
  18 interleaved examples across nine skills, one SGD batch, immutable candidate,
  and four settled evaluation sessions. The model was a generated tiny fixture;
  evaluations used a controlled reference callback. This proves wiring and
  backprop execution, not learned language quality.
- A first fixture with only 256-token context refused the longer byte-encoded
  lessons. Its failure was retained. A separate 2048-context fixture completed;
  no lesson was shortened to obtain that result.

## Wen baselines and the initial capacity refusal

The matched A100 probes used 27 frozen development cases per model/mode, 8192
physical context tokens and 512 output tokens. These were small diagnostics on a
shared GPU, not a formal qualification or a throughput comparison.

| Model | Thinking off | Thinking on | Thinking responses ending at the token limit |
| --- | ---: | ---: | ---: |
| Wen 1 | 6/27 | 3/27 | 24/27 |
| Wen 1.1 | 6/27 | 3/27 | 24/27 |

The 24 limited responses in each thinking run had no final answer. Their scores
measure completion under that output budget; they do not establish that thinking
reduces underlying reasoning ability. Nonthinking runs also contained actual
incorrect composed answers. Original traces and the failed Wen 1.1 launcher
attempt were preserved separately. The launcher failed before inference because
a generated API key began with a dash; the recovery used a new key without changing
the runtime, frozen questions or scoring rules. All serving allocations settled.

For the 375-token maximum practice lesson, PCC's current ordinary native LoRA
planner estimated 336.9 GiB including its reserve. The selected A100 had about
72.7 GiB free. `--admit-training` therefore returned `MEMORY_ADMISSION_REFUSED`
without loading weight tensors, updating a model or writing a candidate. This is
a planner estimate, not measured peak memory, and not a claim that every possible
training implementation needs that much memory.

The first Wen 0.1.2 foundation candidate has now completed one introductory
update (see below). A later three-GPU check admitted and exercised the longest full-pack lesson
(see below). A LoRA or full candidate must pass
separate repair, held-out and retention checks before promotion or release;
a GGUF file alone does not establish those properties.

## Introductory GPU gradient checkpoint and inspectable practice

PCC's opt-in dense sequence profile passed tiny-model LoRA/full updates and
reloads at 64 and 375 tokens on two A100s. A separate 178-token introductory Wen
1.1 lesson passed ordinary LoRA gradient calculation on four A100s. All 498
adapter gradient tensors were finite; 249 were initially nonzero. Wen's base
weights stayed unchanged and the probe wrote no candidate. These are mechanics
results, not evidence of a learned skill or full-pack training capacity.

The owned [108 practice occurrences](../examples/finished-training-examples/foundation-pilot/practice.txt)
are saved as readable question/checked-answer text, with a separate manifest.
There are 107 distinct questions; the repeat is labeled rehearsal. These files
contain no development or blind evaluation questions and no claim of model
success. The actual candidate-serving factory and first guarded live update
have now been exercised as described below.

## First live learning measurement

On 2026-10-23 (local operator date), Wen 1.1 received one ordinary native SGD
update using 18 complete practice examples, two from each of the nine skills.
This was rank-four LoRA, learning rate 0.001, batch size 18, answer/action targets
and thinking off. The longest selected lesson had 177 consumed tokens. The
original base model remained unchanged; the result is a separate 45,426,096-byte
LoRA GGUF, not a released standalone Wen 0.1.2 model.

| Measurement | Before | After |
| --- | ---: | ---: |
| Mean training loss | 0.43516219 | 0.43349394 |
| Protected validation checks passed | 17/54 | 17/54 |

There were zero gained passes and zero regressions, with exactly the same
passing case identities. All nine skills remained below this pilot's requirement.
The candidate was served through PCC for all 54 checks; blind checks were not run
because validation did not qualify. Both serving sessions and native GPU
allocations settled. Native save/reload loss equivalence for this real candidate
is still pending; successful serving is a separate observation.

The adapter SHA-256 is
`ab740f8401a7286e862bf6c37bc4e0237c5d0708a66c6edd552c7ee89573b470`.
The [aggregate result](../validation/foundations-20261023/wen-first-update.json)
contains no protected questions, answers or private paths. Two earlier launcher
failures occurred before inference or training; their fixes were tested separately
and their original failures were retained.

This establishes an actual learning loop and a small training-loss change. It
has not established an improvement in tested capability. Eighteen examples in
one batch are one weight update, not eighteen updates. Useful next measurements
are progressively larger, interleaved practice sets with multiple updates and
unchanged development checks, followed by fresh blind assessment after a
candidate meets the frozen policy. Checkpoints around 100, 250, 500 and 1,000
examples are experiment sizes, not promises about when a skill will appear.

## Full-pack memory and numerical follow-up

The earlier conservative refusal was retained. A later opt-in PCC allocator
check measured the actual tensor-buffer plan before each allocation. The
375-token/26-target maximum lesson passed ordinary LoRA gradient calculation on
three shared A100s, with 498 finite tensors and 249 initially nonzero. Its forward
logits also matched fresh strict FP32 PCC at 350/363/375-token prefixes within the
predeclared maximum-absolute 0.0002 and RMS 0.00005 limits, with the same top token.
No weights were updated in either probe, and all owned allocations settled.
This clears the measured capacity/numerical gate for trying this bounded pack;
it does not establish a capability gain or qualify longer Wen contexts.
