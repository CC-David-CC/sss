# Verify a completed learning loop without running it again

S3 now supplies an owner-run audit of saved PCC/COW learning rounds. A person or
agent can verify the original lessons, native candidates, actual COW answers,
learning/forgetting reports and selected next parent without starting another
inference call or training update. The
[actual MiniCPM qualification](../validation/cow-learning-audit-20261025-bh/README.md)
revalidated two completed rounds and 45 original case records with subprocess
launching blocked. These are mechanics checks, not broad capability acceptance.

## Run the supported audit

Use the qualified Linux runtime and the original owner configuration:

```bash
python -m sss machinery list
python -m sss machinery run cow-learning-audit \
  --pcc-root /qualified/PCC \
  --training-config /private/owner-training.json \
  --cow-profile /private/qualified-base-profile.json \
  --run-id learning-run-001 \
  --output /private/audits/learning-run-001.json
```

The output must be a new file outside the original training store. The service
must have no queued or running work. A busy store or worker is refused; the
auditor does not stop a service, cancel a request, reconcile an uncertain native
update or replace missing evidence with a fresh model evaluation.

Use the original source/input/runtime bindings. A different checkout location
or changed policy implementation can produce a different registered identity,
even when some source bytes match. For a historical source capsule that does
not contain this optional new command, run the new audit file while importing
the original qualified S3/PCC packages:

```bash
PYTHONPATH=/qualified/original-SSS:/qualified/PCC:/qualified/PCC/experimental/branching_context/src \
  python /current-SSS/sss_integration/cow_learning_audit.py \
  --pcc-root /qualified/PCC --training-config /private/owner-training.json \
  --cow-profile /private/qualified-base-profile.json \
  --run-id learning-run-001 --output /private/audits/learning-run-001.json
```

That is how the new public auditor was qualified against the original saved
MiniCPM run. Do not edit a source closure or expected policy ID merely to force
old evidence through a new implementation. A new execution/policy requires its
own explicit qualification and baseline interpretation.

## What it verifies

The auditor reuses PCC's actual operation and lesson readers, S3's registered
COW evaluator recovery and paired analysis, and PCC's optimizer-state and
training-budget receipt validators. It constructs no executor or HTTP service.

It verifies the store's model contract, original run-creation operation, exact
initial-parent approval, derived native-job IDs and completed round order.
Initial same-mode SGD parents can legitimately have no optimizer state; LoRA
parents must retain the approved rank. Each new learning job must use its
registered fresh-state recipe and exact selected parent.

Every lesson is re-tokenized and matched to the independently checked practice
allowed by that policy. The original native request, launch, stdout and zero
exit status must agree with the candidate receipt. Exact supervised examples
must match the optimizer dataset SHA; input/output artifact paths, weights,
moment-state bytes, counters, finite gradients and completed presentations must
match. Recorded native executable hashes describe original provenance; this
is not a claim that a subsequently replaced executable still has those bytes.

The existing COW adapter recovers only complete original backend evidence. It
checks the actual model/hat/runtime, raw token receipts, decoding, EOS behavior,
independent grades and complete case coverage. The audit recomputes each report
against both the original baseline and the selected immediate parent, including
retained-parent/no-gain decisions and assessment proposals.

An audit accepts a completed round boundary or an explicitly stopped prefix
whose next round has no training request, job, pending step or side-effect
artifacts. An ambiguous or started tail requires original-effect reconciliation.
Source files, configuration and records are checked again before success.
No protected questions, answers or raw responses are copied into the summary.

Legacy timed native receipts are interpreted using their actual completed
update count. This introduces no training-time budget: the current controlled
study still compares equal updates and ordered practice presentations.

## Keep audit and execution separate

The audit takes the existing record-admission lock, refuses queued/running
operations, then takes the worker lock. Both acquisitions are nonblocking;
this avoids failing a legitimate queued worker or deadlocking against its
reverse lock order. Existing lock files are opened r+b because NFS exclusive
flocks need a write-capable descriptor. The auditor never writes their bytes.
[Linux documentation](https://man7.org/linux/man-pages/man2/flock.2.html)
explains that filesystem behavior.

The summary records 0 model calls and 0 new native jobs. Missing models, state,
original raw evidence, qualified runtime files or source bindings produce a
refusal rather than a model pass/fail. Audit before retiring required artifacts.
A successful audit validates the measured run and its decision trail; it does
not promote weights, prove mastery, generate new assessment panels or repair a
standalone LoRA merge. Use a new matching assessment to measure new skills.
