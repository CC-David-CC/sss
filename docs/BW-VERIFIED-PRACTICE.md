# A saved BW correction can become an exact practice lesson

S³ can now join a genuine failed BW attempt and its saved correction to an
independent, owner-installed checker. The first supported case is a Python
`task.py` affine-transform, clamp and sum exercise. It is a narrow working path
for building trustworthy lesson intake, not a general proof that arbitrary code
or a model-generated explanation is correct.

BW owns the workflow and its immutable captures. S³ owns the problem, practice
split, independent measurements and lesson derivation. PCC owns the actual model
template, tokenizer, lesson admission and training machinery. The exporter adds
no workflow scheduler and does not run training.

## Three different authorities

1. `branchwrite lesson capture-failure RUN --output NEW_CAPTURE` archives the
   actual stopped attempt, including its exact files, modes, model contract and
   settled workflow receipts. A failure need not have run its own check. The
   archive does not declare independent correctness or authorize training.
2. `branchwrite lesson capture-correction RUN --failure-capture CAPTURE --output
   NEW_CAPTURE` requires BW's existing current passing check and explicit finish.
   The archive links the original failed capture. A passing student-selected
   check is still not an independent S³ verdict.
3. `sss.adapters.bw_verified_practice.export_correction` validates both typed
   archives against an installed owner contract, runs S³'s fixed independent
   oracle on each exact saved artifact, and requires failed `fail` plus corrected
   `pass`. It derives one exact lesson. Owner registration into an approved
   training policy remains a separate decision; an export alone is unapproved.

The independent command runs through BW's existing read-only terminal boundary.
Only the task source and input rows enter that process. Expected results remain
in S³. The reader checks the actual projected source hash, fixed driver and
inputs, raw output, exact JSON types, input preservation and process namespace
retirement. An unavailable or unsettled measurement cannot become a lesson.

## Owner API

Install a `BWArtifactPractice` with an explicit `AffineClampFoldCase`, model
contract, original source hash, supported source mode, practice split and
protected-material descriptors. Its `task_prompt` is the canonical plain problem
specification, including the fixed checker's structural source restrictions. Use
that exact prompt for the BW attempt and its correction. Task aliases or a
different baseline are refused even when a local syntax check passes.

`descriptor()` is private serializable owner configuration. It contains the
closed checker family, exact case rows and protection descriptors;
`from_descriptor()` rebuilds that fixed family without importing arbitrary
checkers. `binding()` supplies hashes for approval records without exporting
hidden oracle rows or protected texts into model prompts.

Construct `PCCArtifactRenderer` from actual PCC `model_text_components`, with
owner-pinned model/tokenizer identity, maximum context and native stop tokens.
`tokenizer_identity(components)` and `binding()` expose the identity data needed
for a separate owner registration. Tokenizer/template/control-token incompatibility
or overflow refuses the export; it never truncates the taught artifact.

```python
exported = export_correction(
    owner, correction_capture,
    correction_capture_id=correction_id,
    failure_capture_id=failure_id,
    renderer=renderer, output=fresh_private_directory,
    target_policy="actions_answer",
)

verified = read_export(
    exported.directory, owner=owner,
    expected_export_id=exported.export_id,
    correction_capture_id=correction_id,
    failure_capture_id=failure_id,
    renderer=renderer,
)
```

`VerifiedBWExport` exposes detached lesson, token/mask and proof data. Its binding
keeps `owner_registered=False` and `training_approved=False`. A policy owner must
approve this exact export and lesson identity rather than accepting a client's
path, arbitrary module, free-form completion or `verified=True` assertion.

## Owner-installed exact lesson membership

`sss.adapters.verified_practice_registry.InstalledBWPractice` loads a private
owner registration. Each row has exactly these keys:

```python
registration = {
    "owner": owner.descriptor(),
    "renderer": renderer.binding(),
    "export_directory": str(verified.directory),
    "export_id": verified.export_id,
    "lesson_id": verified.lesson_id,
    "failure_capture_id": failure_id,
    "correction_capture_id": correction_id,
}
config = {
    "schema": 1,
    "kind": "sss.verified-bw-practice-registry.v1",
    "registrations": [registration],
}
```

Write this owner configuration once to an absolute private file with mode `0600`
or `0400`; do not accept a client-selected configuration or export path. The
POSIX reader opens every ancestor and the file without following symlinks,
checks ownership/mode/size, and refuses aliases, replacements and changing reads.
The configuration may contain protected descriptors and hidden checker rows;
keep it out of Git and model prompts.

Use the same `components` mapping returned by PCC's actual
`model_text_components` call that constructed `renderer`.

```python
from sss.adapters.verified_practice_registry import InstalledBWPractice

provider = InstalledBWPractice(
    absolute_owner_registry_path,
    components=components,
    model_contract_id=owner.model_contract_id,
)
approved_lessons = provider.lessons()
provider.validate_lessons([actual_pcc_stored_lesson_record])
identity = provider.binding()
```

Installation rebuilds only the closed installed checker family and actual PCC
renderer, then calls `read_export`. It requires the exact model, capture, export,
lesson, artifact and token/mask proof. `lessons()`, `verify()` and
`validate_lessons(records, previous_report=None)` revalidate that evidence;
`binding()` returns a detached identity. A changed target, unknown lesson,
duplicate selection or changed registry/source needs a new approval and policy
identity. Additional verification flags cannot add membership.

This provider is staged for a configured learning evaluator. The current CPU
qualification proves actual registry membership and actual PCC schema-2 lesson
admission, including idempotent resubmission and changed-target refusal. It does
**not** connect a production configured learning policy or dispatch training.
That connection must also establish independent target, BW workflow and
retention panels; membership alone cannot measure learning or forgetting.

## What is taught

The initial representation is `final-artifact-v1`: canonical JSON with exactly
`path`, `mode` and `source`. Decoding that object reproduces the complete checked
`task.py` bytes, including a final newline. It teaches the corrected artifact,
not a fabricated sequence of tools, intermediate thoughts or unrelated advice.

The question includes the plain task and the actual failed artifact. Hidden
oracle examples and expected answers do not enter the lesson. Owner-supplied
protected case/split IDs, artifact hashes and text/token substrings are refused
in practice; these checks do not establish semantic independence from every
possible held-out question. Owners must still install genuinely separate cases.

The exporter uses the complete actual PCC rendering. Assistant answer targets
end at the first native EOS. Any trailing template whitespace is retained as
assistant `kind="framing"`, `verified=False`, and always masked. S³ and PCC must
produce exactly the same tokens, targets and masks. Both `actions_answer` and
`verified_thinking_actions_answer` are supported. This artifact-only lesson has
no independently verified thinking, so it teaches no thinking tokens under
either policy.

`sss.lesson_targets` owns the lesson-only framing extension and delegates all
ordinary span validation to the unchanged legacy `sss.profiles` contract. It
does not alter foundation model profiles, arithmetic generators or historical
curriculum identities.

## Revalidation and scope

An export contains both self-contained BW archives, original independent oracle
records and raw output, exact episode content, source/mode inventory, lesson and
token masks. `read_export` requires owner pins, rereads the typed archives,
regrades saved observations, verifies source/helper identities and reconstructs
the lesson and masks. It makes no model, network, oracle-execution or training
call and works after the original operational paths are unavailable.

`finished-training-examples/example.txt` preserves the readable question/answer
pair using S³'s existing completed-record export. It explicitly states that no
model weight update is implied. The reader checks it against the same episode
bytes; it is a handoff view, not a second correctness authority. The surrounding
fixture result identifies its scripted proposals separately.

The source pins include S³'s oracle/export/profile/episode authorities, BW's
actual helper closure, PCC's renderer receipt and its lesson segment validator.
Changing these sources requires a newly verified export and approval rather
than silently relabeling an old artifact. Partial outputs have no completed
export record and must not be registered.

The CPU fixture in `sss_integration/bw_verified_practice_cpu.py` performs genuine
BW read/edit/check/finish actions through PCC's HTTP/COW/grammar/store machinery,
but scripts the proposals with a deterministic byte backend. The local check is
deliberately only syntax; S³ separately establishes the semantic failure/pass
contrast. MiniCPM's actual GGUF header, template and tokenizer are used without
loading tensors or running a forward pass. The fixture is machinery evidence,
not a model capability, training result, or approved lesson.

For a Linux owner test environment with BW and PCC available on `PYTHONPATH`:

```sh
python -B -m unittest -v sss_tests.test_bw_verified_practice \
  sss_tests.test_framing_targets

PCC_MINICPM_GGUF=/owner/model/MiniCPM5-2B-F16.gguf \
  python -B -m unittest -v sss_integration.test_bw_verified_practice

python -B -m sss_integration.bw_verified_practice_cpu \
  --output /owner/evidence/new-joined-probe \
  --model /owner/model/MiniCPM5-2B-F16.gguf
```

The header-dependent tests live under `sss_integration`, separate from the pure
core test suite. Explicitly running them without an owner model path is a setup
error. The fixture requires the real Linux terminal namespace facility and the
existing PCC test-support paths; it supplies no alternate execution runtime.

The [sanitized CPU validation receipt](../validation/learning-program-20261024/bw-verified-practice-cpu-20261026.json)
records source versions, test counts and limits. The full core passed without
BW, PCC or NumPy installed; the optional integration used genuine Linux tool
boundaries and the real MiniCPM tokenizer, with scripted proposals. These are
machinery checks, not model skill scores.
