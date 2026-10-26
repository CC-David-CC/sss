# First mixed native block through BW and PCC

The learning machinery now executed one real full-model update through BW's
client, PCC's authenticated native job API and S³-verified lesson inputs.
It also preserved a named F32 GGUF privately. This proves a native job can consume
the verified mixed batch and save its candidate. The candidate regressed from 438 to 26 correct answers on a new 864-question
review panel. The complete joined assessment also still has an unresolved BW
grammar-stream error; this candidate is not accepted for use.

## Plain-language reading

The machine practiced one code lesson and 27 arithmetic/state review lessons.
It changed the model and saved that version. Its loss on that very practice
batch rose, which is a reason to investigate, not to announce a better model.
Separate answer and retention measurements are now complete: the artifact panel
stayed at 2/2, but review answers fell from 438/864 to 26/864. Nothing has been
promoted or uploaded as model weights.

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
auxiliary learning-rate field is reported explicitly. Its contribution to this
plain-AdamW result has not yet been established; it is not a diagnosed cause of
the loss increase. Nonzero gradients are not a new finite-difference gradient
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
particular full update safe. A next candidate still needs the same behavioral
and forgetting checks. The original base and named rejected candidate remain
unchanged; no learning-run acceptance record was fabricated.
