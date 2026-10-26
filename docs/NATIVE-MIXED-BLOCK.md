# Mixed native learning through BW and PCC

Two real full-model AdamW candidates now passed through BW's client, PCC's
authenticated native job API and S³-verified lesson inputs. Both started from
the same original model and practiced the same 28-example block once. A step
at 0.00001 collapsed review scores from 438 to 26/864. A fresh step at 0.000001
instead measured 446/864: 14 answers gained and 6 lost. Both named F32 GGUFs
remain private. BW workflow coverage is still incomplete; neither candidate
has been promoted or accepted for use.

## Workflow and recovery follow-up

The [recovery guide](WORKFLOW-RECOVERY.md) records a completed native
read/edit/check/finish task with independent verification, a separate proven
2,048-token budget failure, and the storage/capture corrections uncovered by
the campaign. The passing task used explicit recovery and an additional
interpreter-step allowance; it is not a same-bound two-case panel score.
S³ now settles proven budget failures and continues its panel, with archived
read-only evidence. Generic CLI native qualification and a complete joined
learning round remain open. Neither candidate is promoted.

## Plain-language reading

The first version changed too much in one step. Audits found lower-loss points
along that change, so we tried a smaller fresh step from the original model.
That second version did slightly better overall while losing six previously
correct answers. We kept it as a research candidate, with the losses recorded
for future practice using new examples. This is progress in diagnosing and
operating the learning loop, not proof of a broadly better model.

The sections below preserve the first candidate's failure and its investigation.
The second candidate's completed results follow them. Neither result is part
of the frozen ten-arm, 68-update comparison.

## Recorded measurements

| Item | Original record |
| --- | --- |
| Host | llm-60, RTX PRO 6000 Blackwell |
| Update | Ordinary native dense backprop, full AdamW, fresh moments |
| Presentations | One update, all 28 selected examples consumed |
| Review | Nine arithmetic/state skills, one example per mastery gate |
| Main learning-rate field | Approximately 0.00001 |
| Auxiliary learning-rate field in resolved native configuration | Approximately 0.0003 |
| Finite nonzero gradient tensors | 381 |
| Mean training loss before / after | 0.4197256 / 1.2127761 |
| Native terminal receipt | `MECHANICS_EXECUTED`, exit 0 |
| Native receipt's save/reload qualification flag | Original `false` retained unchanged |
| Independent saved-model reload loss check | PASS: absolute difference 6.98e-8, bound 0.0002 |
| Preserved private file | `MiniCPM-S3-mixed-native01-full-F32.gguf` |
| Acceptance / publication of weights | Neither |

The [sanitized native receipt](../validation/learning-program-20261024/native-mixed-block-20261026.json)
retains model, job and preservation hashes. Full-mode rank 2 is an existing
request-schema field; this was a full update, not a rank-2 adapter. The resolved
auxiliary learning-rate field is reported explicitly. Source inspection confirms
plain AdamW uses the main learning rate; the
auxiliary default applies to fallback groups in the Muon path. The component
audit also found no evidence of a larger accidental AdamW step. Nonzero
gradients are not a new finite-difference gradient
check. A saved GGUF is not itself numerical save/reload qualification.

## What the BW attempt established

On the fresh protected target panel, the unchanged starting checkpoint produced
two correct artifacts and both responses naturally finished. In actual BW, the
first task completed `read_file`, `replace`, `read_file`, `run_check`, `finish`;
the independent artifact oracle also passed it.

On the second BW task the model tried to create a file that already existed.
The executor correctly refused that operation. The following attempted full-file
replacement repeated array entries across two settled 256-token response chunks.
A subsequent resume ended with an indeterminate grammar-stream error. The
original journal, completed first case, partial second case and retired server
records remain intact. This is incomplete workflow coverage, not an invented
0/2 score or a claim that every failure was model ignorance.

A CPU-only diagnostic on llm-49 replayed the 512 saved tokens through the exact
original grammar engine identity. Their masks and acceptance passed, including
the next mask calculation. This rules out a deterministic failure in that saved
prefix; it does not reproduce or explain the later failed resume. No model
question was redispatched for this diagnostic.

## Technical and applied interpretation

There are three separate questions: did native optimization execute, did the
candidate survive independent save/reload checks, and did measured behavior
improve without unacceptable forgetting? The first has evidence. The latter two
remain separate measurements. The native job was submitted independently after
the joined run stopped, using the exact already validated mixed lesson block;
the failed learning run was not rewritten into a success.

S³ owns lesson validation, frozen panels and comparisons. PCC owns model
identity, backprop, leases, jobs and immutable artifacts. BW supplies its actual
client journal and file/tool workflow. The 864-question new review before/after
panel and candidate artifact measurement are complete. Their
completed baseline artifact responses are recovered from original evidence,
not generated again. An independent save/reload loss check passed after the
assessment owner retired and the same worker/GPU leases were acquired.

The fixed ten-arm, 68-update optimizer/rank study is unchanged. This mixed block
is separate learning-loop qualification work, not an additional point on those
curves. No seed repeat, model transfer from A100, model upload or promotion was
performed. The joined observe/lesson/train/assess/decide/preserve pathway still
needs its workflow failure and complete acceptance/report behavior resolved.

## Completed paired result

The frozen new review panel measured **438 -> 26 correct out of 864**, with
**5 answers gained and 417 lost**. All 864 responses naturally finished both
before and after. The artifact panel stayed at 2/2. This is a bad candidate,
not an improvement hidden by a formatting or stopping failure. It remains a
private diagnostic; no working parent or published model was advanced.

| Skill (96 questions each) | Before | After | Gained | Lost |
| --- | ---: | ---: | ---: | ---: |
| math.place_value | 26 | 8 | 5 | 23 |
| math.add.no_carry | 95 | 1 | 0 | 94 |
| math.add.carry | 80 | 0 | 0 | 80 |
| math.multiply | 59 | 0 | 0 | 59 |
| math.divide | 60 | 7 | 0 | 53 |
| math.fraction | 32 | 3 | 0 | 29 |
| math.add.signed | 75 | 4 | 0 | 71 |
| state.registers | 1 | 0 | 0 | 1 |
| math.fraction.add | 10 | 3 | 0 | 7 |

The [paired assessment and reload receipt](../validation/learning-program-20261024/native-mixed-block-assessment-20261026.json)
retains result and report hashes. This is a different frozen question set from
the ten-arm comparison; 438 must not be compared directly to that study's
59-answer original baseline. Within this new panel, questions, runtime and
bounds match before and after, and no completed question was generated again.

The first independent reload request was refused before inference because the
operator-side request retained an adaptive-state output field. The corrected
evaluate-only request stripped output/state fields and passed: original loss
1.2127760649, reloaded mean loss 1.2127761347, difference 6.98e-8. No training
update was repeated. That check supports save/reload consistency on these exact
28 masked examples; it is not a proof of universal inference equivalence or a
new gradient finite-difference test.

The native mechanics succeeded while this learning update failed. The loss
increase and paired behavioral losses require investigation before choosing
another update. The current installed optimizer source selects the main learning
rate for plain AdamW; its serialized auxiliary-rate default is not by itself an
explanation. S3's paired retention comparator rejected this candidate. The full
PCC learning-run decision remains incomplete because its BW panel failed; a
standalone comparison must not be rewritten as a completed joined round.

## Why the next check is step size

PCC's new [read-only step audit](https://github.com/CC-David-CC/Private_Context_COW/blob/feat/training-step-audit-20261026/docs/TRAINING-STEP-AUDIT.md)
checked all 2,516,756,480 parameter components and the saved first moment.
There were no nonfinite weights and no violations of the first fresh zero-decay
AdamW component bound. The reconstructed gradient norms matched the native
record within 1.09e-7 relative error. Forward-only loss on the original model
also matched the backward-graph starting loss within 2.60e-8.

The recorded gradient dot actual update was -4.48896, while starting loss was
0.419726. That local linear prediction would drive the loss below zero; it is
not a reliable prediction over the full step. A controlled forward-only probe
then measured fractions of the same observed weight change, without another
backprop pass or held-out question evaluation:

| Fraction of update | Loss on the exact owned 28-example block |
| --- | ---: |
| 0 | 0.419726 |
| 0.01 | 0.379416 |
| 0.10 | 0.281242 |
| 1 | 1.212776 |

Along this update path, the full step passes lower-loss points and ends worse.
This supports an overshoot explanation for this block. It does not establish
that either smaller file improves retention, that every gradient is independently
correct, or that AdamW is generally inferior. The smaller files are temporary
interpolated diagnostics, not registered native training candidates or new
points on the frozen optimizer/rank comparison.

The mixed block contained 310 supervised tokens; 75 belonged to its one code
lesson. Native training averages selected-token loss within each example, then
averages examples. Token counts alone do not measure objective weight or gradient
influence. Even 27 review lessons alongside one code lesson did not make this
particular full update safe. A smaller fresh candidate then received the same behavioral
and forgetting checks, as reported below. The original base and named rejected candidate remain
unchanged; no learning-run acceptance record was fabricated.


## Second candidate: smaller fresh step, measured gain and forgetting

The [second native-candidate receipt](../validation/learning-program-20261024/native-mixed-block02-20261026.json)
records a genuine native full AdamW update at **0.000001**, with fresh optimizer
moments. This is not continued training of the failed first candidate and not
a second random-seed run. The original base hash and 28-example dataset match
the first candidate. Completed baseline answers were reused from their saved
receipts; only the new candidate was assessed.

| Measurement | Original base | Candidate 01, rate 0.00001 | Candidate 02, rate 0.000001 |
| --- | ---: | ---: | ---: |
| Practice loss, same owned 28 examples | 0.419726 | 1.212776 | 0.281242 |
| Review answers correct / 864 | 438 | 26 | 446 |
| Answers gained / lost against original base | — | 5 / 417 | 14 / 6 |
| Naturally finished review responses / 864 | 864 | 864 | 864 |
| Artifact answers correct / 2 | 2 | 2 | 2 |
| Independently reloaded practice-loss difference | — | 6.98e-8 | 9.12e-9 |

Both candidates consumed 28 presentations in one update. Do not draw a
two-update training curve through these columns. Candidate 02's native loss
matches the earlier 0.10 interpolation probe within 1.1e-8; the new GGUF was
produced by actual backprop and the registered native job, not interpolation.

| Skill (96 questions each) | Before | Candidate 02 | Gained | Lost |
| --- | ---: | ---: | ---: | ---: |
| math.place_value | 26 | 32 | 6 | 0 |
| math.add.no_carry | 95 | 95 | 0 | 0 |
| math.add.carry | 80 | 82 | 2 | 0 |
| math.multiply | 59 | 59 | 0 | 0 |
| math.divide | 60 | 59 | 0 | 1 |
| math.fraction | 32 | 29 | 0 | 3 |
| math.add.signed | 75 | 78 | 5 | 2 |
| state.registers | 1 | 1 | 0 | 0 |
| math.fraction.add | 10 | 11 | 1 | 0 |

The net gain is eight answers, about 0.93 percentage points on this particular
development panel. Twenty paired answers changed. This is a descriptive
observation, not statistically established population-level improvement or a
claim about questions beyond this panel. Practice examples are separate from
these questions; raw protected failures have not been exported as lessons.

The existing strict S³ comparator still returns `REJECTED`, because it retains
the answer losses and requires more coverage. That machine decision is preserved.
The owner-authorized research loop can retain a promising candidate and practice
its weaker classes on new examples, while release acceptance and the working
parent remain separate. A policy for advancing such research candidates must
make its tolerance and missing coverage explicit; we have not silently relaxed
the strict comparator or manufactured a completed PCC learning-run decision.

Candidate 02 passed independent save/reload evaluation on the exact same 28
masked examples: native loss 0.2812422513961792, reloaded loss
0.28124224228460143, absolute difference 9.12e-9 against a 0.0002 bound. No
training update was repeated. Its original native receipt's unqualified flag
remains unchanged; this separate check has its own receipt and limited scope.
The private named export is `MiniCPM-S3-mixed-native02-full-F32.gguf`.

The two temporary interpolation GGUFs used to diagnose candidate 01 were retired
after exact-byte checks and confirmation that no process held them open, reclaiming
20,144,343,168 bytes. Their protocols and results remain. Original and named native
candidate models were preserved. No model weights were published or transferred
between A100 and the home fleet.

## BW parser stress: a reproducible infrastructure failure

The [CPU stress receipt](../validation/learning-program-20261024/bw-grammar-stress-20261026.json)
uses the exact original tokenizer, grammar and engine identity. After accepting
the 512 observed response tokens, it appends a **synthetic** repeating continuation
from the saved suffix. At 706 total accepted tokens, the matcher reports
`lexer error: too many states: 250000 >= 250000` and `InternalError`.

This establishes an actual parser resource failure for that constructed input.
It is consistent with a failure during the original third 256-token chunk, but
the unrecorded original suffix is unavailable: it does not prove that identical
tokens caused the original failure. It used no model calls or training updates.
The first BW case's success and the second case's indeterminate operation remain
intact. No unknown operation was resent and no completed question was regenerated.

The next engineering work is to isolate the grammar expansion and provide an
explicit recovery route for parser failure. Repeated text is still useful model
failure evidence; infrastructure exhaustion is not a model-score result, and
simply increasing parser limits would not qualify recovery.


## Supported optional grammar selection in the S³ workflow panel

The BW workflow panel now accepts an optional `"grammar_syntax": "lark"` field
in its **workflow panel owner configuration**. This reaches the actual BW host
launch and is included in runtime identity. Other panel kinds do not acquire
that option. Omitting it retains the previous GBNF launch and request bounds.
Install the matching [PCC](https://github.com/CC-David-CC/Private_Context_COW/blob/feat/lark-grammar-20261026/docs/LARK-GRAMMARS.md)
and [BW](https://github.com/CC-David-CC/BranchWrite/blob/feat/lark-grammar-20261026/docs/LARK-GRAMMARS.md)
feature branches and provide a newly bound, qualified runtime before a native
model assessment; existing live sources and frozen comparison arms are unchanged.

The optional path preserves action and array parser rules while keeping string
lexemes. With the real MiniCPM tokenizer, **all 512 token masks in the observed
prefix matched the old grammar exactly**, with zero differing bits. The new
matcher then accepted that prefix plus 4,096 synthetic tokens without changing
resource limits. The old matcher exhausted its lexer-state allowance at 706
on the constructed continuation. This does not recover the missing original
suffix or prove the precise original-crash cause.

The S³ CPU integration exercised actual BW read/edit/check/finish, failure and
correction captures, preserved-input checks and read-only evidence replay using
the new syntax. A scripted CPU backend supplied the proposals. Native model
forward calls and training updates were zero. Launch tests also show that the
explicit syntax reaches BW without changing grants, task bindings or request
budgets, and unsupported values fail before dispatch. See the
[selection and replay receipt](../validation/learning-program-20261024/lark-workflow-selection-20261026.json).

Fourteen checks passed in the first selection, alongside one test-module naming
error in the invocation. The correctly named child-installation selection then
passed three checks; completed workflow cases were not rerun to fix that loader
error. These are component/integration controls, not a completed native joined
learning round. The old unknown operation remains preserved. Next, qualify the
new source/profile installation and test real model workflows as new recorded
work rather than relabelling that original operation.
