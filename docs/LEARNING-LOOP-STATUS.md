# Learning-loop tooling status

This is the operator's meta-environment record. It is not student curriculum,
training text, assessment prompts, or a model skill score. Improving a checker,
driver or recovery path is a tooling result, not a learned model capability.

## Current state

| Component | Evidence-backed status | Remaining work |
|---|---|---|
| Skill catalog and coverage inventory | 137 nodes; 66 implemented generators; 71 planned, including a nine-node binary reverse-engineering path | Per-gate coverage and explicit mastery evidence, not just implementation labels |
| Foundation generation and checking | Nine-skill study plus preliminary 57-skill independent screen | Qualify broader ranges, reasoning conditions, composition and transfer separately |
| Primitive duplicate handling | Six replacement families with checked references; old results retained | Integrate versioned generators into supported curriculum installation |
| Coding/admin diagnostic connection | Original and Remix 2 executed 11 tasks; isolated code/config checks | Actual BW/native tool pathway and broader Linux administration |
| Lesson verification and mixed review | Existing SSS/BW/PCC installation qualified, including prepared 128-lesson admission | Bind next curriculum to chosen current parent; old prepared policy is not a Remix 2 continuation |
| Native training and checkpointing | Completed fixed 68-update comparisons; exports and archived states retained | Next mixed curriculum not trained yet |
| Answering, formatting and reasoning separation | Matched scalar answer/format/composed panel and verified practice lesson builder implemented; S³ and PCC CPU tests prove separate span masks; native CPU receipt confirms five scalar masks | Extend task-native adapters beyond scalars; run model panel; measure learning and retention |
| BW failure → S³ practice → PCC admission | Controlled fixture path passes; two public shell adapters pass BW launch admission and broken/reference controls | Resolve both pending model operations, then qualify an end-to-end completion/recovery before deriving a lesson |
| Operator next-action guidance | Pure state-to-action helper and guard tests | Connect trusted component receipts; not yet an end-to-end automatic driver |
| Learning/forgetting measurement | Per-skill results, gains/losses, quant and external checks exist | Consolidated current reports and unseen qualification before mastery claims |
| Checkpoint preservation and cleanup | Best/final preservation and verified fleet archival exercised | Continue explicit per-cycle retention receipts and space checks |
| Skill-tree discovery from results | Preliminary 57-leaf screen found weak and unexpectedly strong areas; purpose-specific rewrites added for Boolean, deduction and rounding | Turn each discovery into versioned prerequisite/test/generator change with separate qualification |
| Publication | Models/model card and selected SSS/PCC reports published | Some current mode/screen/guidance changes remain local; reconcile stale training report |

## Track every cycle on two axes

**Student/model:** immutable parent and candidate IDs; curriculum and split IDs;
answer mode; supervised spans; optimizer settings; practice presentations;
per-skill/gate outcomes; format, completion and reasoning checks; retention;
candidate decision and retained artifacts.

**Operator/tooling:** exact source versions and test definitions; harness and native
runtime identities; generator/checker qualification; queue ownership; infrastructure
failures; recovery actions; retries or reused evidence; resource and storage usage;
tool changes; report/publication receipts; outstanding gaps.

Do not blend the two. A checker correction, harness repair, changed token limit or
native gate-policy change must be disclosed as an environment change. Save original
outcomes; rescore existing evidence when valid, otherwise create a new condition.
Do not count a machinery pass as model mastery or an infrastructure failure as a
student failure.

## Recent tooling findings

- The versioned `mixed66-v1` pack was prepared on llm-60 against the verified
  Remix 2 update-42 F32 checkpoint, using PCC's actual renderer, tokenizer, and
  lesson service. It contains 1,584 admitted practice entries (1,506 distinct
  prompts), 396 development cases and 396 qualification cases. It performed no
  training or model assessment. The longest admitted sequence was 555 tokens;
  preparation therefore used PCC's existing `dense-llama-action-8k-v1` profile,
  not the historical 512-token comparison profile. [Preparation receipt](results/mixed66-preparation-20261028.json).
- `sss_integration.mixed66_prepare` checks the content identities of the saved
  864-case study and 64-case external panel before admitting lessons, and checks
  exact prompt overlap against those and a reconstructed 57-skill screen. All
  three had zero exact collisions. This is not a semantic leakage check or a
  complete inventory of every protected test. The reconstructed screen uses the
  current generator and contains repeated prompts. The finite Boolean truth
  tables share underlying inputs across splits despite different wording; the
  tiny two-per-gate sets are triage, not mastery or statistically precise rates.
  [Check receipt](results/mixed66-protected-prompt-check-20261028.json).
- Next: qualify a native training run with this longer sequence profile and the
  selected checkpoint, retain the parent and candidate, and measure both the
  intended skills and independent coding/admin and retention panels. Preparation
  alone does not prove a real-model automatic failure-to-learning cycle.
- A native ordinary-backprop probe on the longest admitted example (555 tokens)
  passed on llm-60: all 381 model parameter tensors had finite, nonzero gradients.
  It made no weight update and is not an assessment of model quality.
  [Gradient receipt](results/mixed66-gradient-probe-20261028.json). The first
  full-model AdamW update separately completed on eight practice entries, and
  its exported candidate reloaded with loss error 3.67e-9. This establishes an
  update and checkpoint round trip, not learning, retention, or promotion. A
  resumed run is intended to cover the first 136 practice presentations.
  [First update receipt](results/mixed66-first-update-20261028.json).

- Initial tool fixture grading demanded unrequested finish wording. Corrected it,
  added regression coverage, and rescored saved trusted observations; no inference
  was repeated and original verdicts remain.
- Six foundation families repeated prompts. Replaced their diagnostic definitions
  according to their primitive purpose; Boolean finite domains remain finite.
- Direct-answer and reasoning-mode metadata are now separate. The metadata helper
  alone is not proof that native training masks or reasoning evaluation are wired.
- A custom diagnostic bridge made actual model attempts possible, but does not
  qualify BW's own workflow or native function-calling behavior.
- The 57-leaf screen exposed apparent regressions/gains and strict-output effects.
  Its 8-item per-skill panels are triage only. Follow-up should inspect raw failures,
  isolate skill demands, and expand unseen cases before lesson choice.
- Boolean truth tables have finite semantic coverage; duplicate wording is not new
  coverage. Rounding uses decimal stimuli to avoid adding fraction-division skill.
- A universal JSON answer wrapper invalidated the first structured-format screen
  for native proof-object tasks. Raw evidence is retained and excluded from model
  comparisons; per-task response schemas are required in the corrected design.
- Answering, formatting, and their composition are separate curriculum levels.
  Earlier strict-output foundation screens cannot tell a skill error from a format
  error. The three-level design and scoring rules are in
  [ANSWER-FORMAT-LEVELS.md](ANSWER-FORMAT-LEVELS.md); no controlled run has
  established those separate rates yet.
- `sss/learning_levels.py` now validates explicit lesson levels and scores the
  answer, format, reasoning and joint results independently. `sss/level_evaluation.py`
  freezes and runs matched numeric-answer triplets, and `sss/learning_lessons.py`
  admits reference-checked practice with separate answer and format spans. The
  corresponding PCC feature adds masks for answer-only, format-only, composed, and
  reasoning-plus-answer targets. The current S³ suite has 156 passing tests on
  Windows (12 skipped) and llm-79 (no skips); 23 PCC lesson-service tests pass, and the native
  CPU proof confirms five response masks. These are machinery checks, not a model
  quality result.
- `sss/suites/code_foundations.py` keeps a triple-function follow-up in a separate
  practice registry. `sss_integration/bw_capture_verify.py` can require an
  independently verified BW failure/correction pair, check the selected practice
  reference, create a provenance-bound S³ archive, and verify PCC's persisted
  tokens and loss mask. This is controlled-fixture evidence; it does not authorize
  training, update weights, or establish a real model capability improvement.
- `sss_integration/bw_practice_native_cpu.py` exercised that exact path through one
  PCC full-weight CPU update: 32 supervised tokens, native mask matched S³,
  candidate loss 5.67208 → 5.66749, base fixture unchanged, and no promotion.
  The generated tiny fixture is not a language model, so loss movement only proves
  that the update executed. Receipt:
  [bw-practice-native-cpu-20261028/result.json](../validation/bw-practice-native-cpu-20261028/result.json).
- Added nine explicitly planned reverse-engineering leaves: a disposable binary
  lab prerequisite, bitwise/XOR/shift/GF(2) foundations, controlled fixture
  generation, layout inference, CRC identification, iterative experiment, and
  cross-version transfer. These placeholders have no environment, generator,
  checker, or proficiency evidence yet; the current inventory marks them planned.
- Corrected a stale curriculum test that expected the current generator to recreate
  the old optimizer-pilot pack ID. The historical report retains its recorded hash;
  new packs are checked against their own complete definition and current generator.
  This matches the documented rule that the old pack is not a continuation for the
  current parent.
- The first real MiniCPM/BW attempt found a PCC frame-check bug: the native MiniCPM
  template preserves leading and trailing user whitespace, but PCC compared against
  `content.strip()`. The PCC feature branch now compares the exact content; 31 focused
  PCC compatibility tests pass. With that correction, MiniCPM read and edited the
  isolated shell fixture, and the independent checker passed there. Review then
  found that our declared verification command pointed to a host path unavailable
  inside BW's isolated shell. BW requires evidence for the exact declared command;
  substitute checks could not satisfy it, so the workflow retried until it exhausted
  bounded steps and hit the pinned COW context limit. This run qualifies the prompt
  compatibility fix and exposes a test-adapter setup defect; it says nothing about
  MiniCPM's shell proficiency or BW's general recovery behavior. The original
  generation remains unresolved after recovery and was not replayed. The model
  weights were untouched and no
  verified BW completion or S³ lesson was recorded. See the sanitized
  [MiniCPM integration result](results/bw-minicpm-integration-20261028.json).

The saved COW profile has an 8,192-token capacity. The first pending request had
5,882 source tokens, 592 input tokens and a 2,048-token output request; the
second had 8,015 source tokens and requested another 2,048. Both sums exceed the
capacity checked by PCC's generation code. The original error receipts are not
available, so this is a supported failure mechanism rather than a proven error
for either request. See the [context investigation](results/bw-minicpm-context-capacity-20261028.json).

PCC and BW now expose an explicit snapshot-bound text context preflight. It uses
the configured encoder for the next text suffix and reports whether the requested
output fits; it does not dispatch model work, automatically change generation, or
compact history. Controlled CPU checks passed 16 PCC and 34 BW tests. These do
not qualify actual long-context model behavior, multimodal inputs, or recovery of
the prior unknown operations. See the [preflight receipt](results/bw-pcc-text-preflight-20261028.json).

BW also offers an opt-in guard for new text runs. It checks each exact request
before model dispatch and stops when the requested input and output cannot fit.
The controlled COW/BW CPU suite passed 72 tests, including continuation, an
interruption before dispatch, and a pending request that must not be replayed.
The guard does not shorten output or compact context. The [guard receipt](results/bw-context-guard-20261028.json)
does not establish model quality or actual long-context operation.

One separate real MiniCPM F16 Python repair completed through guarded BW/PCC on
llm-60. BW recorded verification, S³ independently checked the exact edited
source, and BW exported a payload matching that source. The first workflow step
allowance expired with no pending operations; continuation used the same saved
run and completed. This public development task used 2,977 tokens of a 32,768
token profile, so it is neither a long-context test nor a held-out quality score.
No model failure lesson or training update resulted. The original two unknown
operations remain unresolved. See the [model qualification record](results/bw-minicpm-guarded-python-20261028.json).

The follow-up adapter `sss_integration.bw_task_adapter` materializes the public
`shell.failure_status` and `shell.quoted_filename` fixtures with workspace-relative
inputs. Five tests passed on llm-60, including admission through BW's existing
coding launcher and both commands' broken/reference controls. This is tooling
evidence only: checks are visible, the independent S³ host checker was not
invoked, and the model tasks did not complete. Both original COW operations remain
unresolved and were not replayed. See the [adapter qualification receipt](results/bw-task-adapter-qualification-20261028.json)
and [separate quoted-filename model attempt](results/bw-quoted-filename-attempt-20261028.json).

## Ownership and exclusion

S³ owns coverage, test definitions, checking and curriculum/measurement policy.
BW owns task execution and tool permissions. PCC owns inference, backprop,
candidate identities and native jobs. Operator-side coordination composes their
verified receipts; it must not become a second training engine or BW runtime.

Do not automatically ingest this document, operator notes, hidden references,
protected test responses, or checker internals into student examples. Any future
lesson derived from a tooling incident must be deliberately authored, independently
verified and admitted through the ordinary practice pathway.

Next operator step: investigate and settle both COW operations through their
original recovery paths. Neither may be replayed while unresolved. Do not derive a
lesson until there is a stable verified completion boundary. Then independently
check a completed capture, admit only a separately checked lesson, and measure
unseen transfer plus mixed-skill retention.
Keep feature branches separate; merge to `main` only after the pathway and recovery
behavior are stable.
