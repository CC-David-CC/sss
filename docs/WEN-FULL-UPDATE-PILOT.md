# Wen: one ordinary full-weight update

On 2026-10-24 UTC, Wen 1.1's protected development score changed from **17/54 to
19/54** after one full-weight SGD update. Three answers became correct and one
previously correct answer became wrong. **The candidate failed preservation,
was not qualified and was not promoted.** Its sealed blind checks were not run.

This is a measurable behavioral change in a small pilot. It is not evidence of
broad improvement, formal mastery, a released Wen 0.1.2, or readiness for a day
of autonomous administration or research. Wen is helping test the machinery
that will later support Codi; they are distinct models and roles.

The complete aggregate record, identities and limitations are in
[`wen-full-update.json`](../validation/learning-program-20261024/wen-full-update.json).
Protected questions, answers and private traces are not published.

## What was held fixed and what changed

The candidate started from the original immutable Wen 1.1 BF16 GGUF. The update
consumed the exact same 18 token/target/mask arrays used by the earlier
18-example LoRA pilot: two practice examples from each of nine arithmetic and
state skills, fixed pack seed 20261023, longest input 177 tokens. Thinking was
off; action/answer targets were selected. Validation used the same 54 frozen
development cases, balanced across independent, compositional and recovery
gates, through PCC with matching inference settings.

This run updated all 427 active parameter tensors using ordinary complete-graph
backpropagation and native SGD, without PyTorch. It used one accumulated batch
of 18 examples and learning rate 0.0001. The earlier LoRA run used rank 4 and
learning rate 0.001, so this is **not a learning-rate-matched ablation** between
full updates and LoRA. Neither run changed the original base model.

| Measurement | Original | Full candidate |
| --- | ---: | ---: |
| Mean loss on the 18 practice examples | 0.4351621866 | 0.2650510669 |
| Protected development checks | 17/54 | 19/54 |
| Place value | 3/6 | 2/6 |
| Multiplication | 3/6 | 4/6 |
| Fractions | 0/6 | 1/6 |
| Fraction addition | 0/6 | 1/6 |

The other five skill totals were unchanged. The per-example comparison found
three gained passes, one lost pass and 16 retained passes. A better total
therefore did not satisfy the preservation rule. The guard retained the
original policy and rejected the candidate; it did not lower a threshold or
turn the failed evaluation answer into a practice label.

## Save/reload and resource evidence

The native writer saved the updated active tensors as F32. The GGUF is
**31,876,841,504 bytes** (31.88 GB decimal, approximately 29.69 GiB). The source
BF16 file is 16,244,817,856 bytes. This pilot's candidate remains on the training
host; no GGUF was uploaded or transferred back.

A separate native reload evaluated all 18 practice examples without performing
another update. Reloaded mean loss was 0.2650510510, within the required 1e-5
tolerance of the saved candidate's 0.2650510669. This establishes numerical
save/reload agreement for the measured examples, not general retention.

Training and reload used four shared A100s; the baseline and candidate serving
checks used one A100 each. Conservative stage allocation accounting totals
**0.6216 A100 GPU-hours**, including preparation overhead: stage wall time times
the number of allocated cards. All four stages settled, and no account-owned
GPU allocations remained at settlement. Shared load makes these timings
unsuitable as dedicated-server throughput measurements.

The earlier 375-token full-gradient-only qualification took another 0.0925
GPU-hours and is a separate operation. The full update here used the shorter
18-example control set; it does not establish longer full-update training or
128K-context quality.

## What this tells us to test next

Loss now moves substantially and independent answers can change, so the next
question is whether useful changes survive varied practice and mixed review.
Preserve these exact outcomes, use separately generated practice for the
regressed skill, and compare verified demonstrations and update settings with
frozen evaluation gates. Do not optimize against the sealed blind answers.

Short checks can guide the development series; extended per-domain and sealed
checks are still required before accepting a recipe. Repeated runs with other
seeds are outside the current campaign authorization. The
[harness comparison](HARNESS-COMPARISON.md) holds weights fixed and tests a
different intervention; keep its results separate from this weight update.

## Interpreting the one lost place-value answer

The six-question place-value sample is too small to establish a broad class
regression. [Failure-rate estimation](FAILURE-RATES.md) describes the approved
96-question paired follow-up and a corrected composition generator. Historical
54-case scores retain their original source; they are not regraded.

The completed [larger paired assessment](WEN-PAIRED-ASSESSMENT.md) found 23/96
to 29/96 place-value passes, seven gains and one loss, and unchanged results on
96 review questions. It did not change the original acceptance policy or promote
the candidate. The corrected composition suite has its own source identity.
