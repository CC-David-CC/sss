# Public original-evidence audit qualification

The reusable `cow-learning-audit` machinery suite audited the existing completed
two-round MiniCPM5-2B run on 2026-10-25. It recovered and revalidated all 45
original COW case records, exact lesson/native request/dataset/state bindings,
registered recipes, parent selection and both paired reports. The result stayed
1/15 -> 5/15 -> 5/15 correct and 3/15 -> 9/15 -> 13/15 naturally finished.

[Result](result.json), [actual-model qualification](qualification.json) and
[CPU checks](cpu-checks.json) record the scope and source hashes. Subprocess
launching was deliberately forbidden during the actual audit: 0 launch attempts,
0 new inference calls and 0 new native jobs. This was verification of saved
work, not another training trial or a new model-quality score.

The 67 CPU checks include real filesystem locks, queued/running-work refusal,
corrupt native requests/stdout/state/dataset evidence, initial SGD parents
without moment state, same-mode/rank/artifact approval, retained-parent rounds,
legacy timed receipts and safe stopped prefixes. Their candidate bytes and
decision fixtures are explicitly controlled; they are not language models.

The first shared-filesystem audit attempt opened an exclusive lease read-only
and failed before dispatch. The corrected implementation opens existing lock
files with r+b, never creating, appending or truncating them. This is required
for exclusive flock emulation on NFS; see the
[Linux flock manual](https://man7.org/linux/man-pages/man2/flock.2.html).
Record admission is locked first, queued/running jobs are refused, and the
worker lock is acquired nonblocking to avoid disrupting a queued training job.
Original failure evidence was retained. No numerical or acceptance gate changed.

[Owner and agent procedure](../../docs/COW-LEARNING-AUDIT.md). Broader skill,
standalone model and release acceptance remain separate.
