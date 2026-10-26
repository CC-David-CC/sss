# MiniCPM update-curve progress snapshot

Initial capture: 2026-10-26 01:53-01:54 UTC. This is an interim results note, not an acceptance report. Time-stamped refreshes below update the saved progress as work continues.

## Live status refresh — 2026-10-26 02:03 UTC

- **A100 is reachable.** An 8-GPU `nvidia-smi` snapshot returned at 02:03:50 UTC. The exact per-arm score table below remains the latest verified A100 completion table; no newer A100 evaluation receipt was confirmed during this refresh. A100 resource records at 01:57 show several jobs waiting for GPU admission. The snapshot also showed heavy shared load on GPUs 3, 4 and 5 (100%, 98% and 97% utilization), so waiting is consistent with contention. No A100 study crash was confirmed.
- **llm-60 is still working.** At 02:02 UTC, its COW evaluator was evaluating AdamW full update 40. The latest completed receipts remain AdamW update 39 (488/864) and standard Muon, RMS/decay Muon and fast/refine Muon at update 38. The RTX PRO 6000 showed about 90% utilization with 9.7 GiB occupied in that snapshot. This is active evaluation, not a stuck training process.
- **No model has been accepted or promoted.** Both the fixed comparison and rank sweep are incomplete. This refresh adds machine/process observations, not new model scores.

## Latest verified checkpoints — 2026-10-26 02:11 UTC

These are the newest saved per-arm progress records I could verify. A100's progress files were current through 02:01-02:03; llm-60's newest completed evaluation was AdamW update 40. The current numbers below replace the 01:54/01:53 snapshot tables that follow; those earlier tables remain to show what was known at that time.

### Original fixed-68 comparison

| Host | Arm | Latest complete update / 68 | Example presentations | Correct / 864 |
| --- | --- | ---: | ---: | ---: |
| A100 | Full AdamW | 44 | 1,188 | 474 (54.9%) |
| A100 | Full standard Muon | 46 | 1,242 | 489 (56.6%) |
| A100 | Full RMS/decay Muon | 44 | 1,188 | 482 (55.8%) |
| A100 | Full fast/refine Muon | 41 | 1,107 | 464 (53.7%) |
| A100 | AdamW LoRA rank 16 | 55 | 1,485 | 498 (57.6%) |
| llm-60 | Full AdamW | 40 | 1,080 | 483 (55.9%) |
| llm-60 | Full standard Muon | 38 | 1,026 | 466 (53.9%) |
| llm-60 | Full RMS/decay Muon | 38 | 1,026 | 464 (53.7%) |
| llm-60 | Full fast/refine Muon | 38 | 1,026 | 478 (55.3%) |

The next saved llm-60 score is actively being evaluated: standard Muon update 39. On A100, several arms have recent `waiting-resource` records, so a saved score can lag behind the live GPU snapshot. A100 and llm-60 are separate runs, not repeat seeds, and their scores must not be pooled as repeats.

Some checkpoints moved down on the same 864-case suite: A100 LoRA16 went from 501 at update 54 to 498 at update 55; A100 fast/refine Muon went from 466 at update 40 to 464 at update 41; llm-60 AdamW went from 488 at update 39 to 483 at update 40. These are score decreases, not crashed processes. Per-case gains and losses are needed to explain what changed.

### Extended LoRA-rank sweep on A100

| LoRA rank | Latest complete update | Example presentations | Correct / 864 | Naturally finished / 864 |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 12 | 324 | 207 (24.0%) | 739 |
| 2 | 16 | 432 | 285 (33.0%) | 797 |
| 3 | 14 | 378 | 289 (33.4%) | 825 |
| 4 | 14 | 378 | 317 (36.7%) | 855 |
| 8 | 18 | 486 | 376 (43.5%) | 863 |

These are still early and uneven practice counts; they do not yet establish the best rank. The sweep remains separate from the fixed 68-update comparison.

At about 02:11 UTC, the shared A100 snapshot showed 98% utilization on GPU 0, 100% on GPU 3 and 97% on GPU 4. Several arms had entered `waiting-resource` states. On llm-60, the RTX PRO 6000 was evaluating with about 9.3 GiB occupied; the latest snapshot showed 34% utilization. No training candidate has been accepted or promoted.

## What was measured

The model is MiniCPM5-2B. Each score below is the number of correct cases out of the same 864-case held-out set. Training progress is reported in updates and example presentations, not wall-clock time. Each update contains 27 presentations. The historical starting model scored 59/864 (6.8%) and naturally finished 415/864 responses on this suite.

The original comparison has five arms, each planned for 68 updates: full-weight AdamW, standard full-weight Muon, RMS/decay Muon, fast/refine Muon, and AdamW LoRA rank 16. A100 and llm-60 are separate run roots. No full model checkpoints were transferred between them. llm-60 carries the four full-weight optimizer arms; the LoRA and rank sweep are on A100.

## Original fixed-68 comparison: historical 01:53-01:54 checkpoints

### A100 (01:54 snapshot)

| Arm | Latest complete update / 68 | Example presentations | Correct / 864 |
| --- | ---: | ---: | ---: |
| Full AdamW | 44 / 68 | 1,188 | 474 (54.9%) |
| Full standard Muon | 46 / 68 | 1,242 | 489 (56.6%) |
| Full RMS/decay Muon | 44 / 68 | 1,188 | 482 (55.8%) |
| Full fast/refine Muon | 40 / 68 | 1,080 | 466 (53.9%) |
| AdamW LoRA rank 16 | 54 / 68 | 1,458 | 501 (58.0%) |

### llm-60 (01:53 snapshot)

| Arm | Latest complete update / 68 | Example presentations | Correct / 864 |
| --- | ---: | ---: | ---: |
| Full AdamW | 39 / 68 | 1,053 | 488 (56.5%) |
| Full standard Muon | 38 / 68 | 1,026 | 466 (53.9%) |
| Full RMS/decay Muon | 38 / 68 | 1,026 | 464 (53.7%) |
| Full fast/refine Muon | 37 / 68 | 999 | 478 (55.3%) |

These are intermediate checkpoints at unequal update counts, so they do not identify a winning optimizer. In particular, the A100 and llm-60 scores are not pooled as if they were repeats of one identical run. No candidate has been promoted.

At 01:53 UTC, llm-60 AdamW update 39 had a complete held-out score. A Muon fast/refine update 38 native training step was active at 01:49 UTC, and one held-out evaluator was active at 01:53 UTC. The other llm-60 arms remain below update 39; their controllers are separate from the A100 jobs.

## Extended LoRA-rank sweep on A100 (01:54 snapshot)

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

## Current interpretation and next gates (updated 02:11 UTC)

- The 68-update comparison is incomplete on both hosts. Latest verified A100 checkpoints span updates 41-55; llm-60 spans updates 38-40. One llm-60 evaluation and multiple A100 resource waits were observed during the 02:03-02:11 checks.
- The rank sweep is incomplete and has unequal practice counts. Latest verified points span updates 12-18. Compare ranks at matched presentations after collecting more updates.
- Preserve the answer-level gains and losses at every update. A higher aggregate score alone is not enough to accept a candidate if it forgets protected skills.
- Finish evaluation, settlement, and exact artifact checks before making a model-acceptance or export decision.

The hash-pinned per-run receipts and private machine/process inventory are retained separately. This public note intentionally contains aggregate results only.
