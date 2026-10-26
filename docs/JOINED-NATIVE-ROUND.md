# A measured native learning round across BW, PCC and S³

One bounded round completed the joined path: approved lessons entered through
BW's COW client; PCC owned the native training job, evaluation phases, decision
and named export; S³ validated practice and measured learning and forgetting.
The new candidate did worse overall. The system retained the previous working
model and preserved the rejected candidate privately for diagnosis.

This round is separate from the frozen ten-arm, 68-update optimizer/rank study.
It uses a different 864-question review panel. Do not combine their scores.

| Panel | Cases | Before correct | After correct | Answers gained | Answers lost |
| --- | ---: | ---: | ---: | ---: | ---: |
| Final code artifact | 2 | 2 | 2 | 0 | 0 |
| Actual BW tool workflow | 2 | 1 | 1 | 0 | 0 |
| Arithmetic/state retention | 864 | 479 | 459 | 21 | 41 |
| Total | 868 | 482 | 462 | 21 | 41 |

Both checkpoints naturally finished 867 of 868 responses/workflows. A closed
unverified BW attempt remains a failure; it is not an independently verified
artifact success. Its original tool and model receipts remain private.

## What trained, and what did not

The installed starting weights were an earlier learned research candidate.
PCC applied one ordinary dense full-model AdamW update, at learning rate
0.000001, with explicitly fresh optimizer moments. All 28 selected presentations
were consumed: one independently checked code correction and one review example
for each of nine arithmetic/state skills at each of three mastery gates.
No PyTorch backend, model-seed repeat or fixed training-time comparison was used.

The teacher used scripted proposals executed through actual BW tools and an
independent artifact oracle on owned practice. The tested model did not discover
that correction itself. The exported code lesson teaches the final artifact,
not the complete BW tool trajectory. The two target artifact tests already
passed before this update, so their continued success is not evidence of a
newly learned capability. Workflow success did not improve either.

The training loss fell from 0.31888136 to 0.31824476. A separate forward-only
reload of the saved candidate measured 0.31824474 on the same last 28-example
batch: absolute difference 1.34e-8, below the existing 0.0002 bound. The check
applied no update and left the weights, optimizer state and original operation
records unchanged. It is a new diagnostic receipt, not a retroactively invented
predispatch completion/recovery intent. Last-batch mean-loss agreement does not
establish all-position logit equivalence or broad model quality.

## Decision and preservation

S³'s working-parent policy can keep useful net gains while reporting losses for
repair; the stricter release gate is separate. This candidate had no target or
workflow gain and a net loss of 20 review passes, so the working parent stayed
unchanged. A diagnostic named F32 GGUF was preserved privately as
`MiniCPM-S3-joined-candidate03b-full-F32`. Neither weights nor protected responses
were uploaded, and no candidate was promoted or accepted for release.

The [sanitized measured receipt](../validation/learning-program-20261024/joined-native-round-20261026.json)
retains per-skill/gate paired counts, immutable identities and the independent
reload result. It contains no protected question text, answers or case IDs.

## Rechecking the original evidence

The read-only auditor validates the registered policy and completed round
boundary, original lessons and native request, candidate/state hashes, exposure
cursor, saved case evidence, recomputed reports and exact working-parent choice.
It takes the original record/worker leases and refuses active work. It never
constructs a learning service executor or launches another model training/evaluation.

An original audit exposed a reporting bug: it expected answer deltas at the top
level, whereas a joined panel report stores them under `aggregate`. The fix
compares the entire report with freshly recomputed analysis before extracting
the aggregate and each panel's summary. It does not flatten away panel failures,
change an assessment, relax a gate or rewrite the original failed audit.

Use the original installation paths and owner configurations when auditing a
saved run. Moving them into a different checkout changes source/path identities.
An updated auditor can run outside that frozen installation while importing the
original evaluator sources through `PYTHONPATH`:

```sh
python /updated-sss/sss_integration/cow_learning_audit.py \
  --pcc-root /original-pcc \
  --training-config /owner/audit-config.json \
  --cow-profile /owner/original-review-profile.json \
  --run-id original-learning-run-id \
  --output /owner/new-read-only-audit.json
```

The owner configuration names the existing private `directory`, unchanged
`runner`, original `learning_config` and original `max_tokens`. It grants no new
GPU work. Keep it private. Missing evidence or an identity mismatch is an
operator hold; inspect the original job instead of rerunning it under a new ID.

Sixty-two CPU controls passed, including flat and wrapped reports, multiple
rounds, no-dispatch/source-immutability checks, nested-report tampering, missing
backend evidence, lease conflicts and actual panel composition contracts.
The wrapped-report fixture is explicitly a report-shape control, not native
training. The supported audit CLI then revalidated this actual native round: **1,736
original case records**, one native update and its saved optimizer state, exact
paired reports and the retained-parent decision. It started zero model calls or
new native jobs and changed no original evidence. Its source hash and result
are retained in the sanitized receipt.

The full reusable system remains unfinished. Repeatable multi-round native
operation, verified tool-trajectory practice, broader skills and sealed release
qualification still need evidence beyond this bounded round.
