# Wen: the larger paired assessment

The one-update full-weight candidate passed **29 of 96 fresh place-value
questions**, compared with **23 of 96** for the original Wen 1.1. Seven answers
changed from wrong to correct; one changed from correct to wrong. On another
96 questions across eight review skills, both models passed the same 36
questions. This is encouraging development evidence, with substantial remaining
uncertainty and low absolute performance. **The candidate remains unpromoted.**

The [aggregate evidence](../validation/learning-program-20261024/wen-paired-place-value-96.json)
contains rates, Wilson intervals, paired comparisons, source/model identities,
evidence hashes and resource accounting. Raw questions, answers and traces stay
private. No training occurred during this assessment.

## Why a larger assessment was needed

The [original full-update pilot](WEN-FULL-UPDATE-PILOT.md) passed 17/54 before
training and 19/54 afterward, but lost one of six place-value successes. Six
questions could identify a particular regression; they could not establish a
general decline across place value. The operator approved a fresh 96-question
place-value assessment, plus a smaller review screen for the other eight skills.

All 192 questions were frozen before either model answered. Previously used
practice, development and blind cases were excluded; duplicate underlying
problems were removed before inference. The original and candidate answered
exactly the same questions, with the same PCC runtime, temperature zero,
sampling seed zero, thinking off, 8,192-token context and 512-token output limit.
There were no different-seed repetitions or harness rewrites. The candidate is
the unchanged F32 checkpoint from the original single full-weight update.

Preparing the new set exposed and corrected a composition-generator defect:
old place-value composition cases were direct digit questions. New composition
cases require calculating a nested expression before selecting a digit from
its result. Both models used that corrected suite. Historical 54-case results
retain their original generator and grading; the absolute scores of the two
suites are not interchangeable.

## Outcomes and uncertainty

| Place-value gate | Original passes | Candidate passes | Newly correct | Newly wrong |
| --- | ---: | ---: | ---: | ---: |
| Independent | 9/32 | 12/32 | 3 | 0 |
| Composition | 4/32 | 7/32 | 4 | 1 |
| Transfer and recovery | 10/32 | 10/32 | 0 | 0 |
| Equal-weight total | 23/96 | 29/96 | 7 | 1 |

The measured failure rate fell from **76.0% to 69.8%**, a 6.25-percentage-point
decrease on this declared generated curriculum. Individual Wilson 95% intervals
are approximately 66.6–83.5% and 60.0–78.1%. The exact paired two-sided McNemar
calculation gives **p = 0.0703125** for the seven gains and one loss. This does
not meet a conventional 0.05 threshold; it also does not establish equivalence
or absence of improvement. The intervals describe the declared distribution,
subject to independence and representativeness assumptions, rather than all
everyday arithmetic. See [failure-rate interpretation](FAILURE-RATES.md).

The eight exploratory review skills had 12 cases each, four per gate. No
question changed pass/fail status. Those small samples cannot establish broad
retention or equivalence. Transfer/recovery in the primary skill did not improve.
Formal mastery, long-context learning, tool use and research competence were
outside this assessment. The sealed blind evaluation was not run.

## Decision and next experiment

Keep the candidate and its evidence for research. The original strict
preservation decision remains rejected; the larger sample does not erase the
old lost success or silently change the adoption policy. A useful total gain
and a particular regression are both visible here.

The next weight-training experiment should use separately generated varied
practice and verified demonstrations, with mixed review of the earlier skills.
Its frozen development checks should retain prior successes and test transfer.
The protected questions from either assessment must not become practice labels.
Declare a new experiment and its bounds before modifying a candidate; do not
resume the settled operation or increase its budget in place. Harness changes
belong to the separately controlled [harness comparison](HARNESS-COMPARISON.md).

## Resources and audit

Two sequential sessions on one shared A100 consumed **0.4803 allocation
GPU-hours**: 823.9830 seconds for the original and 905.1267 seconds for the
candidate, including conservative session overhead. Before them, a failed
operator attempt answered zero questions because it acquired the same GPU lease
that PCC needed; that attempt settled and was charged another 28.4175 GPU-seconds
(0.0079 GPU-hours). The corrected operator used a separate lifetime lease.

The export independently recomputed all skill/gate statistics from the paired
observations and checked completed settlement. No account-owned GPU inference
process remained at audit. Shared contention limits timing comparisons. Both
models and the F32 candidate remain on the A100 host; no GGUF was transferred or
uploaded. This assessment did not change any weights or promote a model.
