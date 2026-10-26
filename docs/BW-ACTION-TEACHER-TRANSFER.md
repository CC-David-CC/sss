# Teach a student from independently checked BW actions

S³ can now export a correction produced by a human, another agent, or an
owner-authored script for a different student model. The source capture keeps its
original model/backend identity. The student receives newly rendered text and
tokens from its own PCC tokenizer and chat template. This is an explicit owner
operation; a model cannot request arbitrary lesson installation.

This pathway extends [BW action practice](BW-ACTION-PRACTICE.md). It does not
change the frozen 68-update comparison, install lessons automatically, start
training, or claim that a scripted teacher is a model-generated demonstration.

## What is verified

The source BW failure and correction must still have their original, matching
task, project baseline, file modes and capture IDs. The independently executed
S³ artifact oracle must find the failed artifact incorrect and the corrected
artifact correct. The currently supported workflow is the recorded
`read_file → replace → run_check → finish` repair of `task.py`.

For each action, PCC reconstructs the original append-only history with the
student's actual renderer. Earlier teacher actions and all tool feedback stay in
context with loss disabled. Only the current action and its native EOS are
supervised. No source byte-token IDs are reused as student token IDs, and no
lesson is shortened to fit. Context overflow is an explicit refusal.

The teacher's name and category are **owner declarations**. The verifier proves
the captured actions, independent correctness checks, student rendering and
exact lesson membership; it does not independently establish who authored the
teacher's text. `owner-scripted` accurately describes the CPU qualification.
That qualification uses real BW/COW/OS boundaries and real GGUF metadata, but
performs no model inference or training.

## Prepare an owner declaration

Use the original source `BWArtifactPractice` descriptor and capture IDs. Obtain
the student's exact model contract from the intended PCC installation, rather
than substituting a model filename or inventing a contract. In an owner-side
Python process with the matching S³/BW/PCC source available:

```python
from sss.records import digest, canonical
from sss.adapters.bw_verified_practice import BWArtifactPractice
from sss.adapters.bw_action_practice import BWActionTeacherTransfer

owner = BWArtifactPractice.from_descriptor(source_owner_descriptor)
transfer = BWActionTeacherTransfer(
    source_owner_sha256=digest(owner.binding()),
    source_model_contract_id=owner.model_contract_id,
    student_model_contract_id=student_model_contract,
    failure_capture_id=failure_id,
    correction_capture_id=correction_id,
    teacher_kind="owner-scripted",  # or "human" or "agent", as actually declared
    teacher_identifier="my-checked-repair-script-v1",
)
```

Save `transfer.descriptor()` as private owner JSON, using an exclusive write and
mode `0600`, as for the existing owner configuration. It pins the source owner,
source and student contracts, both captures, and declared teacher. Changed pins
require a new declaration and new export, not editing an old receipt.

## Export and audit

Run the existing owner command with the additional private transfer descriptor:

```sh
python -m sss.adapters.bw_action_practice export \
  --owner /private/source-owner.json \
  --teacher-transfer /private/teacher-transfer.json \
  --model /models/student.gguf \
  --correction-capture /private/correction \
  --correction-capture-id CORRECTION_SHA256 \
  --failure-capture-id FAILURE_SHA256 \
  --directory /private/new-student-export \
  --maximum-tokens 8192 --stop-token-ids 1 130073
```

The stop IDs above are the qualified MiniCPM configuration, not universal IDs.
Use the actual student's admitted stops, renderer and context bound. S³ reads
GGUF metadata here; it does not load a native inference model. Preserve the
returned export ID. For audit, replace `export` with `audit`, omit
`--correction-capture`, and supply `--export-id EXPORT_SHA256` with the same other
inputs. Audit reads the embedded capture and checks the saved independent oracle
evidence without re-executing tools or oracle programs.

The exported `finished-training-examples/example.txt` preserves the complete
question/action/observation history privately. Keep this and the original
receipts on disk; do not publish private workspaces, answers or credentials.

## Install exact student lessons

Use the existing owner-only `sss.verified-bw-practice-registry.v1` configuration.
For each of the four turns, retain the original source owner descriptor and add
`teacher_transfer: transfer.descriptor()` to its registration, alongside the
existing renderer, export directory/ID, lesson ID, capture IDs and `turn_index`.
The registry's `model_contract_id` is the **student** contract. Registration
rechecks the source evidence, declaration, student rendering and exact lessons;
omitting the transfer does not silently permit a model mismatch.

An export remains `owner_registered=false` and `training_approved=false`.
Owner installation supplies exact membership for the configured evaluator; it
does not bypass target, BW workflow, retention, memory, optimizer or candidate
acceptance checks. Install a new policy and baseline when source closures or
membership change. Old jobs and historical results retain their original pins.

## What remains before a learning claim

The CPU qualification proves transfer/export/registry behavior, including CLI
export and read-only audit. Real MiniCPM gradient/resource qualification is
reported separately in PCC's
[real action memory report](https://github.com/CC-David-CC/Private_Context_COW/blob/feat/dense-llama-attention-recompute-20261026/docs/REAL-ACTION-RECOMPUTE-MEMORY.md).
Neither proves that a student improved. That requires actual owner installation
with the real student contract and protected split manifests, native adaptive
training, independently assessed target and BW behavior, mixed retention tests,
and a recorded acceptance or rejection. Recovery and a named private model
artifact remain part of that complete round.
