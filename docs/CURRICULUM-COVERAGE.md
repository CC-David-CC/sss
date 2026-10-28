# Curriculum coverage: 28 October 2026

This map describes the MiniCPM fixed 68-update comparison and subsequent Remix 2
diagnostics. It is not a claim that no earlier Wen/model experiments occurred.
Catalog status, training exposure, test coverage and mastery are distinct.

## Inventory

| State | Count | Meaning |
|---|---:|---|
| Catalog nodes | 128 | Entire current catalog, including planned work |
| Implemented generator nodes | 66 | Exact-foundation generators exist; not proof of model mastery |
| Nodes practiced in the fixed comparison | 9 | Eight arithmetic skills plus register tracking |
| Other implemented nodes outside that comparison | 57 | Preliminary individual baseline now measured with 8 cases each; weak subskills need redesigned/expanded tests |
| Planned catalog nodes | 62 | Do not count as implemented training/evaluation coverage |

Do not interpret these as 128 terminal graph leaves. The graph includes prerequisites,
branches and convergence nodes. No curriculum-wide mastery claim is established.

## Nine trained skills

Each skill has 96 development questions: 32 independent, 32 composition and 32
transfer/recovery. These questions were not used as practice targets, but the same
development set was observed repeatedly while choosing checkpoints. A fresh unseen
qualification is still required. The original FP32 was retested with the same
recorded runtime as the rank-32 AdamW assessments and again scored 59/864.

| Skill | Original FP32 /96 | Rank-32 AdamW u42 /96 | u68 /96 | Remaining issue |
|---|---:|---:|---:|---|
| Addition with carrying | 0 | 92 | 84 | High development score; still needs fresh qualification |
| Addition without carrying | 0 | 95 | 94 | High development score; still needs fresh qualification |
| Signed addition | 0 | 91 | 87 | High development score; still needs fresh qualification |
| Division | 0 | 64 | 61 | u42 composition gate 0/32 |
| Fractions | 48 | 58 | 61 | Weak across gates; u42 20/18/20 |
| Fraction addition | 0 | 14 | 12 | Weak; u42 9/0/5 across gates |
| Multiplication | 0 | 59 | 57 | u42 composition gate 0/32 |
| Place value | 11 | 30 | 37 | Weak; u42 15/6/9 across gates |
| Register/state tracking | 0 | 0 | 0 | All three gates failed |
| Total | 59/864 | 503/864 | 493/864 | Local gains do not establish general improvement |

u42 naturally finished 864/864 responses versus the original's 415/864.
Scores combine correct answers, requested output form and stopping behavior.
Zero is not proof that the original model has no arithmetic knowledge.

## Other implemented foundation branches

These were outside the nine-skill comparison. Their separate preliminary screen
used eight development questions per skill, direct-answer independent gate. Original
FP32 scored **47/408**; Remix 2 scored **165/408**. Treat every per-skill score as a
triage signal only: eight cases are too few for mastery or stable failure-rate claims,
and strict answer-format checks can conflate formatting and knowledge. An implemented
generator alone does not prove that its mathematical range or escalation has been
fully qualified.

Early Remix 2 triage examples: decimal addition 8/8, decimal multiplication 7/8,
decimal division 7/8, subtraction without borrowing 8/8, subtraction with borrowing
8/8; polynomial derivative 0/8, variance 0/8, linear systems 0/8, signed subtraction
0/8. Test each with larger unseen and format-controlled panels before choosing lessons.
The original had 8/8 on unit conversion and probability, while Remix 2 scored 8/8 and
7/8 respectively. This suggests retention and transfer vary by skill; it does not
establish a general causal comparison from eight examples.

- Elementary arithmetic: subtraction with/without borrowing and signed subtraction;
  absolute value, equality/comparisons, min/max, remainder, powers, floor/ceil/round.
- Decimal and fraction branches: decimal add/subtract/multiply/divide; fraction
  comparison, subtraction, multiplication and division.
- Ratios, percentages and units: ratio; percent-of/change/reverse; unit conversion.
- Geometry: area, perimeter, triangle area and volume.
- Statistics/probability: mean, median, variance, probability and Bayes.
- Algebra/calculus/linear algebra: linear equations/systems, polynomial values and
  derivatives, quadratic roots/minimum, definite integrals, dot products, matrix
  products, determinants, eigenvalues and method selection.
- Logic: AND/OR/NOT/XOR, deduction, joint premises, proof, premise robustness and
  reverse support.

The machine-readable inventory lists each ID and prerequisite in
[curriculum-coverage-20261028.json](results/curriculum-coverage-20261028.json).

## Practical model diagnostics

These tasks were tested after training, not trained in the nine-skill block.
They do not change the catalog's planned status or establish broad skill mastery.

| Diagnostic | Original FP32 | Remix 2 FP32 | Status |
|---|---:|---:|---|
| Simulated read, missing-file recovery, config repair and log diagnosis | 4/4 | 4/4 | Small custom action protocol; not native tool calling or BW |
| Isolated Python/shell repair | 5/5 | 5/5 | Independent execution checks; no broad coding mastery claim |
| Isolated INI configuration repair | 1/2 | 0/2 | Invalid config from appending protected filename |

See [probe evidence and grading correction](ADMIN-MODEL-PROBE.md). No live system
services, packages, networking or host process administration were tested.

Broader retention is a concern: the separate 64-question external diagnostic
scored original FP32 47/64 versus Remix 2 FP32 27/64, including GSM8K 23/32
versus 3/32. This is a small nonrandom sample, not a general benchmark or a
license to train directly on the test questions.

## Remaining work, in order

1. Freeze the completed study; preserve its original failures and gate-policy history.
2. Establish baseline measurements for remaining implemented foundations, with
   prerequisite order and per-gate results. Keep unseen qualification separate.
3. Prepare independently verified new practice for weak composition, place value,
   fractions and state tracking, plus untouched elementary branches and mixed review.
4. For every weak leaf, inspect failed response/checker evidence and ask whether the
   test isolates its named skill. Rewrite ambiguous or conflated cases, keep each
   version pinned, and assess again on untouched variants. Do not copy test answers
   into lessons. Use separate practice/assessment variations for coding, config and tool tasks;
   the diagnostic solutions and test questions are not themselves a new practice batch.
5. Bind the chosen parent checkpoint and curriculum to the supported SSS/BW/PCC
   learning stack. The old prepared 128-lesson round was not dispatched and targets
   a different action-study parent; do not silently reuse it for Remix 2.
6. Train a bounded candidate batch, measure each targeted skill and retention
   domain, report gains/losses, preserve candidate/parent, then select the next batch.
7. Expand actual BW/native-tool and Linux admin coverage before claiming those
   catalog branches are implemented or mastered. Research and other planned branches
   require their own environments and independent checks.

No new post-comparison training round has run yet. The next work is coverage and
verified practice preparation followed by the supported training/evaluation cycle.
