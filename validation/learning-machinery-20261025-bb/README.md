# Durable learning machinery: CPU qualification

Read the [four-level explanation and applied guide](../../docs/LEARNING-MACHINERY.md).
The [machine-readable summary](summary.json) binds source and native executable hashes,
measured fixture outcomes, recovery assertions, and subprocess output hashes.

## Scope and observed result

Three actual CPU native AdamW jobs, 16 updates each, use generated ordinary-Llama
F32 weights and independently checked constant-token classification. Actual
native forward logits give 0/4 → 2/4 → 4/4 → 4/4. Training prefixes and assessment
prefixes differ. No semantic scores are injected. S3 keeps the first two
improvements and retains the preceding parent on no gain. The base is unchanged.
A private full-weight preservation request is exercised; no weights are published.

Both actual BW and PCC clients use authenticated PCC HTTP. The fixture reopens
the service between rounds and exercises the original request journals. Covered
fault injections occur at specific Python boundaries: creation intent before
run-file commit, complete evaluation before phase commit, saved native intent
before dispatch, and submitted native job before phase/acknowledgement commit.
The original IDs/evidence are recovered without a second native update. These
are controlled boundary interruptions, not universal power-failure guarantees.

Additional checks cover stale revisions, untrusted score fields, retired-policy
history, altered historical reports, and late dispatches that must not rewind a
newer phase. The summary records each assertion. Missing original evidence is
an operator problem; it is never replaced by invented results.

## Regression checks

| Check | Result |
| --- | --- |
| Existing PCC lesson/client/optimizer tests | 39 passed, no skips (qualified context import path) |
| Existing BW lesson tests with S3 optional fixture import configured | 9 passed |
| S3 decisions/CLI/composite/growth tests | 17 passed |
| Durable actual-native three-round fixture | PASS, 48 updates |
| Existing full-weight optimizer native job check | PASS |
| Existing registered LoRA native client check | PASS |
| Existing parent-binding native client check | PASS |
| S3 optional machinery/policy imports without NumPy/BW/PCC imports | PASS |

The first BW invocation lacked its S3 fixture on PYTHONPATH and failed at import.
That result remains in the summary; configuring the required sibling import made
the actual nine-test run pass. There was no code change or weakened assertion.
The first PCC run skipped an optional context fixture; configuring its source
path passed all 39 tests without skips. Both invocation receipts are retained.
Native checks reused the recorded existing CPU executable. This Python-only
integration does not claim a fresh CUDA/HIP/SYCL build or deploy changes into the
running fixed-study snapshots. CPU timings are not performance claims.

## Boundaries

The four classifier cases are integration evidence, not language-model mastery.
Bounded classification completion is not natural generation stopping. The
assessment planner is tested independently and generates proposals, not new
questions. Owner-installed policies are programmatic; ordinary service JSON
configuration and full real-model multi-round qualification remain pending.
This machinery suite is not part of the fixed 68-update optimizer comparison.

Reproduction commands and current limits are in the applied guide. Use a new
owned output directory and the qualified native executable. Private operation
stores, generated models, raw subprocess traces, host paths, and credentials
remain outside Git.
