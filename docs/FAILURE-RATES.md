# Estimating a skill's failure rate

Thirty-two varied questions are useful as a quick screen. About 100 questions
per skill give a useful first estimate; around 400 are needed for roughly
five-percentage-point precision. These are approximate 95% planning margins
near a 50% failure rate, assuming representative independent questions:

| Questions per skill | Approximate margin |
| ---: | ---: |
| 32 | ±17 percentage points |
| 96 | ±10 points |
| 100 | ±10 points |
| 400 | ±5 points |

Actual reports use [Wilson intervals](https://itl.nist.gov/div898/handbook/prc/section2/prc241.htm),
which stay inside 0–100% and behave better for small samples or extreme rates
than a symmetric normal interval. A fixed generated curriculum estimates
performance on that curriculum's distribution. Rewording one underlying problem
many times does not supply the same evidence as independent varied problems.
Per-gate results remain visible; an equal-weight aggregate is a declared
curriculum mix, not the frequency of problems in everyday use.

Compare the original model and candidate on the **same** fresh frozen cases.
Report how many changed from wrong to correct and from correct to wrong, as
well as each model's failure rate and interval. The optional exact two-sided
McNemar calculation conditions on these discordant pairs. It is descriptive;
it does not automatically accept a model or replace the preservation policy.
Overlapping individual rate intervals are not themselves a test of the paired
difference. Estimating a small difference between models can require many more
questions than estimating either model's rate to ten-point precision.

The [full-update pilot](WEN-FULL-UPDATE-PILOT.md) used six development questions
per skill. Its place-value score changed from 3/6 to 2/6, with one lost success.
That establishes a changed answer to a particular item. It is not enough to
establish a broad decline in place-value ability. The strict preservation guard
rejected adoption while retaining the candidate and its evidence for repair.

## Completed expanded assessment

The [paired assessment report](WEN-PAIRED-ASSESSMENT.md) records 23/96 to 29/96
place-value passes, seven gains and one loss, and unchanged outcomes on 96 review
questions. The candidate remains unpromoted. The approved design used **96 fresh place-value questions**, 32 each for
independent performance, composition and recovery. Twelve fresh checks for each
of the other eight skills provide a smaller review screen. This is 192 questions
per model and 384 model executions, with fixed model sampling. Twelve-case review
results have wide uncertainty and are not extended qualifications.

Freeze the complete set before either model answers. Exclude previous practice,
development and blind questions, remove duplicate underlying cases before
freezing, and retain selection provenance. No outcome-based redrawing and no
different-seed model repetitions are part of this study. Place value is the
primary question; the eight review skills are exploratory. Neither weights nor
harness instructions change between the paired assessments.

## Correcting composition coverage

Preparing this assessment exposed a generator defect: old place-value cases
labeled `composition` still asked for a digit of a provided number. Version 2
requires evaluating a nested expression before selecting a digit from its
unprovided result. Its mathematical checker independently verifies that the
stored number agrees with the expression. A test reproduced the previous
missing composition and now checks the corrected behavior and corrupted payloads.

This changes the generated family and source identity. Existing frozen training
packs and the published 54-case pilot keep their original source and labels as
historical evidence; they are not silently regenerated or regraded. The new
paired assessment measures both original and trained weights on the corrected
suite. Its absolute scores should not be directly substituted into the earlier
54-case result.

After the paired assessment, repair practice should use independently generated
examples from the affected class plus mixed review. Keep the original failed
test question out of training. Measure whether gains survive and prior successes
return before considering adoption.
