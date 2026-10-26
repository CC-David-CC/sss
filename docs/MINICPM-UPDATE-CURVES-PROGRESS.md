# MiniCPM update-curve progress snapshot

Captured 2026-10-26 01:53-01:54 UTC. This is an interim results note, not an acceptance report. The fixed comparison and the rank sweep are still running.

## What was measured

The model is MiniCPM5-2B. Each score below is the number of correct cases out of the same 864-case held-out set. Training progress is reported in updates and example presentations, not wall-clock time. Each update contains 27 presentations. The historical starting model scored 59/864 (6.8%) and naturally finished 415/864 responses on this suite.

The original comparison has five arms, each planned for 68 updates: full-weight AdamW, standard full-weight Muon, RMS/decay Muon, fast/refine Muon, and AdamW LoRA rank 16. A100 and llm-60 are separate run roots. No full model checkpoints were transferred between them. llm-60 carries the four full-weight optimizer arms; the LoRA and rank sweep are on A100.

## Original fixed-68 comparison: latest completed checkpoints

### A100

| Arm | Latest complete update / 68 | Example presentations | Correct / 864 |
| --- | ---: | ---: | ---: |
| Full AdamW | 44 / 68 | 1,188 | 474 (54.9%) |
| Full standard Muon | 46 / 68 | 1,242 | 489 (56.6%) |
| Full RMS/decay Muon | 44 / 68 | 1,188 | 482 (55.8%) |
| Full fast/refine Muon | 40 / 68 | 1,080 | 466 (53.9%) |
| AdamW LoRA rank 16 | 54 / 68 | 1,458 | 501 (58.0%) |

### llm-60

| Arm | Latest complete update / 68 | Example presentations | Correct / 864 |
| --- | ---: | ---: | ---: |
| Full AdamW | 39 / 68 | 1,053 | 488 (56.5%) |
| Full standard Muon | 38 / 68 | 1,026 | 466 (53.9%) |
| Full RMS/decay Muon | 38 / 68 | 1,026 | 464 (53.7%) |
| Full fast/refine Muon | 37 / 68 | 999 | 478 (55.3%) |

These are intermediate checkpoints at unequal update counts, so they do not identify a winning optimizer. In particular, the A100 and llm-60 scores are not pooled as if they were repeats of one identical run. No candidate has been promoted.

At 01:53 UTC, llm-60 AdamW update 39 had a complete held-out score. A Muon fast/refine update 38 native training step was active at 01:49 UTC, and one held-out evaluator was active at 01:53 UTC. The other llm-60 arms remain below update 39; their controllers are separate from the A100 jobs.

## Extended LoRA-rank sweep on A100

These rank arms were added after the original five-arm plan. Each point below is an independently completed 864-case evaluation, but the ranks have seen different numbers of updates and presentations. Do not read the table as a controlled rank leaderboard.

| LoRA rank | Latest complete update | Example presentations | Correct / 864 | Naturally finished / 864 |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 12 | 324 | 207 (24.0%) | 739 |
| 2 | 15 | 405 | 279 (32.3%) | 790 |
| 3 | 13 | 351 | 284 (32.9%) | 798 |
| 4 | 14 | 378 | 317 (36.7%) | 855 |
| 8 | 17 | 459 | 378 (43.8%) | 863 |

Rank 1 and 2 had substantially more non-finishing answers at these early checkpoints. More updates and matched-presentation comparisons are needed before drawing a capacity conclusion.

## What is running and resource limits

The 01:47 UTC census found all ten A100 study owners alive. At 01:54 UTC, three evaluation workers and four native training workers were active on A100. At 01:53 UTC, one held-out evaluator was active on llm-60. No arm failure or lost owner was reported. This is a live-process snapshot; an arm between evaluations may be waiting for its next admitted step.

A100 GPU utilization and free VRAM in one shared-load sample at 01:49 UTC:

| GPU | Utilization | Free VRAM |
| ---: | ---: | ---: |
| 0 | 51% | 59.1 GiB |
| 1 | 7% | 38.6 GiB |
| 2 | 0% | 73.9 GiB |
| 3 | 100% | 28.7 GiB |
| 4 | 28% | 13.7 GiB |
| 5 | 11% | 52.6 GiB |
| 6 | 32% | 24.6 GiB |
| 7 | 26% | 58.2 GiB |

This is a point-in-time shared-server observation at 01:49 UTC. GPU timings are not used to rank the arms and may be affected by other users' jobs. The A100 host reported about 215 GiB free in its shared-memory filesystem and about 2.3 TiB free in the study home mount. llm-60 reported about 126 GiB free in its home filesystem and about 10% utilization on its single GPU during the active Muon fast/refine training step. These are capacity observations, not proof that every arm can claim those resources.

## Current interpretation and next gates

- The 68-update comparison is incomplete on both hosts. A100's latest complete points are updates 40-54 across the five arms; llm-60 is at updates 37-39. A100 had three evaluations and four training workers active at 01:54 UTC; llm-60 had one evaluator active at 01:53 UTC.
- The rank sweep is incomplete and currently has unequal practice counts. Its latest complete points are updates 12-17. Rank 2 update 16 had not produced a completed score by 01:54 UTC. Continue it, then compare ranks at matched presentations.
- Preserve the answer-level gains and losses at every update. A higher aggregate score alone is not enough to accept a candidate if it forgets protected skills.
- Finish evaluation, settlement, and exact artifact checks before making a model-acceptance or export decision.

The hash-pinned per-run receipts and private machine/process inventory are retained separately. This public note intentionally contains aggregate results only.
