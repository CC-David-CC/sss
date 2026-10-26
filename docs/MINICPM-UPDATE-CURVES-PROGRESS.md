# MiniCPM update-curve progress snapshot

Captured 2026-10-26 01:24-01:29 UTC. This is an interim results note, not an acceptance report. The fixed comparison and the rank sweep are still running.

## What was measured

The model is MiniCPM5-2B. Each score below is the number of correct cases out of the same 864-case held-out set. Training progress is reported in updates and example presentations, not wall-clock time. Each update contains 27 presentations. The historical starting model scored 59/864 (6.8%) and naturally finished 415/864 responses on this suite.

The original comparison has five arms, each planned for 68 updates: full-weight AdamW, standard full-weight Muon, RMS/decay Muon, fast/refine Muon, and AdamW LoRA rank 16. A100 and llm-60 are separate run roots. No full model checkpoints were transferred between them. llm-60 carries the four full-weight optimizer arms; the LoRA and rank sweep are on A100.

## Original fixed-68 comparison: latest completed checkpoints

### A100

| Arm | Latest complete update / 68 | Example presentations | Correct / 864 |
| --- | ---: | ---: | ---: |
| Full AdamW | 43 / 68 | 1,161 | 476 (55.1%) |
| Full standard Muon | 46 / 68 | 1,242 | 489 (56.6%) |
| Full RMS/decay Muon | 42 / 68 | 1,134 | 464 (53.7%) |
| Full fast/refine Muon | 39 / 68 | 1,053 | 464 (53.7%) |
| AdamW LoRA rank 16 | 53 / 68 | 1,431 | 498 (57.6%) |

### llm-60

| Arm | Latest complete update / 68 | Example presentations | Correct / 864 |
| --- | ---: | ---: | ---: |
| Full AdamW | 38 / 68 | 1,026 | 489 (56.6%) |
| Full standard Muon | 37 / 68 | 999 | 465 (53.8%) |
| Full RMS/decay Muon | 37 / 68 | 999 | 466 (53.9%) |
| Full fast/refine Muon | 37 / 68 | 999 | 478 (55.3%) |

These are intermediate checkpoints at unequal update counts, so they do not identify a winning optimizer. In particular, the A100 and llm-60 scores are not pooled as if they were repeats of one identical run. No candidate has been promoted.

At 01:29:37 UTC, llm-60 AdamW update 39 had completed native training and candidate reload; its held-out evaluation was still running. It is not yet a scored checkpoint.

## Extended LoRA-rank sweep on A100

These rank arms were added after the original five-arm plan. Each point below is an independently completed 864-case evaluation, but the ranks have seen different numbers of updates and presentations. Do not read the table as a controlled rank leaderboard.

| LoRA rank | Latest complete update | Example presentations | Correct / 864 | Naturally finished / 864 |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 10 | 270 | 177 (20.5%) | 650 |
| 2 | 14 | 378 | 272 (31.5%) | 788 |
| 3 | 12 | 324 | 276 (31.9%) | 790 |
| 4 | 13 | 351 | 303 (35.1%) | 849 |
| 8 | 16 | 432 | 379 (43.9%) | 860 |

Rank 1 and 2 had substantially more non-finishing answers at these early checkpoints. More updates and matched-presentation comparisons are needed before drawing a capacity conclusion.

## What is running and resource limits

At the 01:27 UTC A100 process census, all ten registered study owners matched their exact process identities and seven evaluators were active. The other three controllers were alive but had no evaluator child at that instant, so they were not doing evaluation work; no failure was reported. Follow-up rank and optimizer evaluations continue independently.

A100 GPU utilization and free VRAM in one shared-load sample at 01:27 UTC:

| GPU | Utilization | Free VRAM |
| ---: | ---: | ---: |
| 0 | 98% | 61.3 GiB |
| 1 | 85% | 31.7 GiB |
| 2 | 17% | 64.3 GiB |
| 3 | 100% | 27.8 GiB |
| 4 | 43% | 12.9 GiB |
| 5 | 37% | 55.6 GiB |
| 6 | 55% | 24.1 GiB |
| 7 | 17% | 60.0 GiB |

This is a point-in-time shared-server observation. GPU timings are not used to rank the arms and may be affected by other users' jobs.

## Current interpretation and next gates

- The 68-update comparison is incomplete on both hosts. A100 is between updates 39 and 53 across its five arms; llm-60 is at updates 37-38, with AdamW 39 evaluation underway.
- The rank sweep is incomplete and currently has unequal practice counts. Continue it, then compare ranks at matched presentations.
- Preserve the answer-level gains and losses at every update. A higher aggregate score alone is not enough to accept a candidate if it forgets protected skills.
- Finish evaluation, settlement, and exact artifact checks before making a model-acceptance or export decision.

The hash-pinned per-run receipts and private machine/process inventory are retained separately. This public note intentionally contains aggregate results only.
