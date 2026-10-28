# Actual-model configured COW learning qualification

On 2026-10-25 the owner-configured learning pathway completed two real native
MiniCPM5-2B LoRA rounds through authenticated PCC HTTP and both the BW and COW
CLI clients on a shared A100. S3 used the existing shared-prefix COW evaluator.

| Stage | Correct / 15 | Naturally finished / 15 | Previously correct answers lost vs baseline |
| --- | --- | --- | --- |
| Baseline | 1 | 3 | - |
| Round 1 | 5 | 9 | 0 |
| Round 2 | 5 | 13 | 0 |

Each round used one native AdamW update over three independently checked
synthetic practice demonstrations. Rank 16, learning rate 0.0001, exact model
renderer, 512-token context and batch, 64 generated-token limit. The five elementary
math skills have three separate gates each. This intentionally small machinery
panel does not establish skill mastery, broad improvement or release acceptance.

Round 2 continued the exact prior adapter with fresh optimizer state, rather
than resuming moments. Its answer total stayed flat, but four additional
responses naturally finished; the paired policy therefore kept it as the next
working parent. All candidates remain unpromoted. The fixed 68 study is separate.

The post-run audit reconstructed the configured policy and checked all 45 raw
case records, token/stop/decoding receipts, exact model and adapter identities,
completed child settlements and both paired reports. It recovered the completed
original evaluations without launching model work and rejected an injected raw
grade change made in memory. Eleven repeated CLI acknowledgements matched;
there were exactly two native jobs. Raw prompts, responses, answers, machine
paths and credentials remain private.

The first audit attempt expected the policy label `fresh-per-job`; the actual
receipt says `fresh`. Correcting that audit expectation required no training or
new evaluation. Original execution and audit-failure records were retained.

[Machine-readable summary](summary.json) includes source and artifact hashes.
[Owner setup and limits](../../docs/CONFIGURED-COW-LEARNING.md) explains the
configuration. The CPU recovery suite additionally covers live original
processes, missing/failed receipts, altered raw evidence and incomplete results.
