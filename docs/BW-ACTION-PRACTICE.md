# Teaching a checked BW tool sequence

The joined learning round taught a corrected file. That is useful code practice,
but it does not directly teach the model how to read, edit, check and finish in
BranchWrite. This optional adapter exports those actual tool turns as lessons.

The first CPU integration produced four examples with 3,029, 3,663, 4,278 and
4,873 input tokens. Their selected targets were 14, 108, 88 and 19 tokens,
respectively, including the native stop. The record and completed training text
were preserved privately. This was scripted CPU machinery through real BW,
COW, file tools, an isolated behavior check and independent S³ grading, with the
real MiniCPM GGUF tokenizer and template. It used no model forward pass or
backprop. Its model contract is an explicitly synthetic fixture identity.

## Who does what

* BW's `captured_action_turns` validates the original context bootstrap, closed
  logical model outputs, consumed native receipts, actual admitted tool arguments
  and settled tool outcomes. It reads existing evidence without tool or network
  dispatch. This export cannot drive or resume a workflow.
* S³ requires an owner-installed practice case and a captured failure/correction
  pair. It independently checks the failed and corrected files, enforces split
  protection, and derives the teaching examples. A passing BW-selected check
  alone is insufficient. Initial support is the owned affine-clamp family and
  one read/edit/check/finish sequence; broader task families are unfinished.
* PCC supplies the real tokenizer, template, initial-user append and stopped-turn
  append rules. S³ verifies the complete lesson tokens against that append-only
  history and exports PCC schema 2. The native engine still owns training,
  allocation, model identities, checkpoints and completion recovery.

The CPU fixture's proposals come from a deterministic byte backend. Its byte
token IDs are never passed off as MiniCPM tokens. The logical recorded text is
rendered anew through PCC's actual MiniCPM append API. This proves the export
mechanics, not that MiniCPM generated a successful trajectory.

## What is trained

Each example contains the real bootstrap and all observations available before
the action. Earlier teacher actions remain exact context, but are masked. Only
the current JSON tool action and its native EOS are selected. Tool observations,
system instructions and framing are always masked. Later tool outcomes and the
independent oracle's answers do not become input to an earlier action.

The final finish-request JSON is the completed episode's `answer` segment. It
is still a tool request; no fabricated conversational answer is appended. The
adapter currently requires non-thinking trajectories. It does not create or
claim verified reasoning targets. Both existing target policies remain available
elsewhere in the learning system.

S³ also saves `finished-training-examples/example.txt` beneath the private
export. It contains the question/action/observation series so a person can read
what was taught. Neither that text nor raw captures belong in a public commit.

## Reproduce the CPU machinery

Use compatible source checkouts on an authorized Linux host. Put S³, BW, PCC,
PCC's `experimental/branching_context/src` and its
`experimental/branching_context/tests/implementation` on `PYTHONPATH`. The latter
is needed only by the explicitly scripted fixture. Provide a local qualified
MiniCPM GGUF; this command does not download or load its inference weights.

```sh
mkdir -p private
python -m sss_integration.bw_action_practice_cpu \
  --model /absolute/path/MiniCPM5-2B-F16.gguf \
  --output "$PWD/private/action-practice-001"
```

The output directory must be fresh. Inspect `result-public.json` and
`export/finished-training-examples/example.txt`. Readback must work after the
original BW workspace is hidden. The fixture installs its exact four lessons in
a private CPU registry only; it neither authorizes production training nor
changes the serving model.

For an actual owner-selected practice capture, use the owner-side command:

```sh
python -m sss.adapters.bw_action_practice export \
  --owner /private/owner-practice-descriptor.json \
  --model /absolute/path/model.gguf \
  --correction-capture /private/correction-capture \
  --correction-capture-id CORRECTION_SHA256 \
  --failure-capture-id FAILURE_SHA256 \
  --directory /private/fresh-action-export \
  --maximum-tokens 8192 --stop-token-ids 1 130073
```

Those stop IDs are the qualified MiniCPM values, not universal model defaults.
Use `audit` instead of `export` to verify existing evidence, supply its exact
`--export-id`, and omit `--correction-capture`. Audit rechecks original oracle
observations and derives tokens again; it does not rerun commands or inference.
The private descriptor is `BWArtifactPractice.descriptor()`. Its model contract,
practice split and protected material must come from the owner configuration.

The existing `InstalledBWPractice` registry accepts an action row with the usual
owner/export/capture/renderer/lesson pins plus an integer `turn_index`. All four
rows can name the same immutable export with different indices. Duplicate
indices, Boolean indices, changed runtime-source pins and altered lesson bytes
are refused. Installation is a separate owner action, rather than an outcome a
student can assert.

## Qualification still needed

The 512-token `dense-llama-short-v1` native training profile cannot admit these
3k–5k examples. A larger renderer limit is only an export bound; it does not
qualify a larger native graph or grant GPU capacity. The next native work must
qualify real MiniCPM allocation on a separate longer-context profile, then run
the target/workflow/retention panels through the existing joined learning driver
with saved-model completion recovery enabled. PCC now provides
[`dense-llama-action-8k-v1`](https://github.com/CC-David-CC/Private_Context_COW/blob/feat/dense-llama-actions-20261026/docs/DENSE-LLAMA-ACTION-TRAINING.md),
with actual 8,192-token tiny CPU/CUDA forward/backward qualification, independent
gradient checks and actual longer-context HTTP job/reload/continuation tests.
The initial profile was added in `49042ec9400b48c760e3281539ccdf8d5e199402`.
Deep ordinary-Llama graphs also require the arena correction in
`a323af12d0154b9b559a1b5719524bade697ad67`; the earlier source alone still refuses
deep examples beyond 512 tokens. These establish native mechanisms, not real
MiniCPM learning or fit. The fixed 68-update comparison stays unchanged.

No improved BW model score, successful native action training, production
acceptance, thinking trajectory, image trajectory, retry/fork flattening or
arbitrary-task support is established by the CPU result. Original captures also
remain pinned to their original BW implementation; this feature does not silently
reinterpret an older capture under a different validator.

## Real-model memory observations

PCC has now completed a read-only 3,663-token full-gradient probe on the learned
MiniCPM parent: all 381 gradient tensors were finite and nonzero, with a sampled
process peak of about 83 GiB on the dedicated RTX PRO 6000. The longer 4,873-token
full and rank-16 LoRA graphs, and an allocation-only 8k extension, exceeded that
one GPU's budget and were refused before graph-buffer allocation. No real model
weights were updated in these checks.

The [PCC memory report and graph](https://github.com/CC-David-CC/Private_Context_COW/blob/feat/dense-llama-actions-20261026/docs/MINICPM-ACTION-MEMORY.md)
separate sampled resident memory, planned graph buffers, persistent optimizer
state and resource refusals. These are current implementation costs, not intrinsic
minimum memory requirements for all ways of training a small model. The next
learning round needs qualified placement for its whole lesson block; summing free
VRAM or passing persistent admission alone does not prove that the graph fits.

## Multi-GPU mechanics and export readiness

PCC's generated tiny-model standard-backprop check now passes on two A100s.
The existing independent FP64 full/LoRA controls and update/reload checks passed,
and all 381 gradient-tensor norms in a 42-layer, 1,024-token graph agreed with the
saved single-GPU reference within 4.77e-7. This measures tensor norms, not every
component, and it is not real MiniCPM learning. The
[PCC two-GPU qualification](https://github.com/CC-David-CC/Private_Context_COW/blob/feat/dense-llama-actions-20261026/docs/DENSE-LLAMA-ACTION-TRAINING.md#two-gpu-standard-backprop-qualification)
records its exact scope and reproduction command. Actual real-model placement
and optimizer-state residency still need their own evidence before the next
action-learning round starts.

PCC also repaired the independent rank-one GGUF weight auditor: a valid singleton
A dimension had been omitted in serialization. The already-written real rank-one
F32 merge then passed a complete independent FP64 audit of 2,516,756,480 weights,
with maximum error 7.28e-8 under the unchanged 2e-7 bound. The successful native
merge was reused; no training or inference was repeated for that repair. Read the
[audit report](https://github.com/CC-David-CC/Private_Context_COW/blob/feat/dense-llama-actions-20261026/docs/RANK1-MERGE-AUDIT.md).
Saved-weight correctness and completed behavioral/retention acceptance remain
separate gates. Neither this audit nor the tiny two-GPU proof approves a model.
