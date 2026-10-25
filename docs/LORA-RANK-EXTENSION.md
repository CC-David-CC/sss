# LoRA ranks 1, 2, 3, 4, 8, and 16: additive 68-update study

Status: all six ranks now have a completed first-update native/COW assessment.
Rank 1's CUDA error is repaired in an isolated build; its exact saved adapter and
optimizer state also continued through native update 2 with independent reload.
The full 68-update curves are still running. The original five-arm study keeps
its existing questions, practice and execution snapshots.

## ELI5

We are giving six copies of the same model different-sized learning hats.
Each copy gets the same ordered practice and the same questions after every
update. This asks how small the hat can be while still learning and retaining
useful skills. It does not shrink the underlying model.

## Engineering summary

Add AdamW LoRA ranks **1, 2, 3, 4, and 8** alongside the existing rank **16**.
Each new arm starts from the same original MiniCPM5-2B F16 artifact, trains for
68 updates with effective batch 27, and uses the unchanged ordered 864-example
practice dataset. Each update is independently reloaded and assessed on the
same frozen 864 development questions through the original COW shared-prefix
path. Learning rate and AdamW settings come from the rank-16 protocol. Native
adapter alpha equals rank, giving alpha/rank = 1 in every arm.

The new arms have independent stores, receipts, native states, resource
reservations, and progress. Existing arm owners, questions, practice, source
snapshots, and states are not edited or restarted. New workers use the existing
GPU locks and resource budget. An unavailable GPU is a wait; uncertain work is
not silently retrained. An individual arm failure must not stop the others.

## Research interpretation

This tests rank under the declared matched recipe, not the best possible tuned
result for every rank. Changing rank changes parameter count, factor shapes,
and the resulting initialization; this is not a campaign of repeated seeds.
The native initialization rule remains unchanged. Plot every matched update,
paired answers gained/lost, completion, and mixed retention. Record native cost,
state size, and adapter size as outcomes rather than using training time as the
organizing budget.

All six LoRA curves use direct immutable adapters over the same F16 base and
qualified per-lease COW runtime. Check the recorded runtime identities before
collating results. The full-weight curves and precision controls retain their
existing distinct runtime/baseline interpretation. No numerical-equivalence or
merge bound is relaxed. A successful direct-adapter assessment is not evidence
that a baked standalone GGUF passes the separate merge/deployment gate.

The addition is five independent arms: **340 more update assessments**, or
**293,760 additional case outcomes**, plus native updates, reload checks, and
milestone evidence. These outcomes are repeated measurements of fixed cases,
not 293,760 independent questions or a blind final evaluation. The 864-example
practice array is cycled as in the parent protocol; count presentations, not
unique examples, when interpreting further exposure.

## Applied controls and current scope

Parent protocol ID:
`667eaafe5dfc24bcc48a93e17350351c6080a5985f196761fe7503ad7f08ee9b`.
Parent protocol file SHA256:
`9fcec8be6ed985f6e8762e583703022d0ea338a5e0822c7d21c46c52a965f2a0`.
Frozen additional-controller source SHA256:
`db2ac3332279fc541602e55bddd1503c3ac806d21067da0c56789cea75787b5e`.

The owner has private launch intents and exact process identities for each
rank, plus per-arm execution amendments. These are fleet operational records,
not a new product runtime. The first native steps qualify the new ranks against
the existing finite-gradient, optimizer-counter, and direct-reload bounds before
held-out scores are reported. Preserve failed evidence and original requests.

Keep milestone adapters/states and measured best candidates under the existing
retention policy. No model publication, A100-to-LAN full-model transfer, or
implicit LoRA merge is authorized by this extension. The supported reusable
learning-run pathway is being integrated separately; this study continues on
its frozen evaluator to preserve comparability.

See the [existing curves and runtime caveats](COW-SHARED-ROOT-LEARNING.md),
[learning machinery guide](LEARNING-MACHINERY.md), and
[actual-model registered LoRA resume probe](REGISTERED-LORA-MODEL-PROBE.md).

Initial independent reload-loss errors for ranks 2, 3, 4, and 8 were approximately
1.13e-7, 4.59e-7, 2.65e-8, and 5.34e-7, respectively, against the unchanged
2e-4 bound. Each completed native update consumed 27 practice presentations.
These are numerical reload checks, not model-quality scores. The rank-1 error
was SGEMM argument 10 (`ldb`) in the ggml CUDA outer-product path. Rank one is
mathematically valid; a separately qualified backend repair has now passed native training,
reload and actual COW scoring. No original library is patched underneath running workers.

Follow-up: the already-open [llama.cpp PR #30142](https://github.com/ggml-org/llama.cpp/pull/30142)
by **edenfunf**, commit `fdb4a0553f6ecb00450f04cc8da5b2b38dd9146d`,
addresses the singleton `OUT_PROD` leading-dimension mechanism. We reproduced
the crash without that patch on llm-49, then passed 103/103 upstream operator
cases against the CPU reference after applying it. The broader matrix-gradient
suite still has numerical comparison failures under investigation; it is not
reported as passing. Actual A100 rank-one native training, reload, first COW assessment and
recorded-state continuation now pass the stated checks below.
PCC keeps the original patch author and commit in its dependency patch provenance.

[Our operator qualification checkpoint](../validation/cuda-outprod-20261025-be/README.md) retains the passing target and unresolved broader checks separately.

## First matched update: early observations

Original: 59/864 correct, 415/864 naturally finished. Each row below has the same
27 practice presentations, AdamW rate 1e-4 and alpha/rank 1.

| LoRA rank | Correct / 864 | Naturally finished / 864 | Original answers gained / lost | Original completions gained / lost |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 60 | 418 | 1 / 0 | 8 / 5 |
| 2 | 61 | 455 | 2 / 0 | 49 / 9 |
| 3 | 63 | 478 | 4 / 0 | 72 / 9 |
| 4 | 66 | 487 | 7 / 0 | 84 / 12 |
| 8 | 100 | 582 | 41 / 0 | 181 / 14 |
| 16 | 154 | 631 | 95 / 0 | 228 / 12 |

These are early recipe observations, not a tuned capacity ranking. Equal rate,
practice and alpha/rank do not guarantee equal update magnitude or equivalent
optimization difficulty across factor shapes. The first rank 1 update makes
one additional answer correct; its completion total rises by 3 while 8 cases
start finishing and 5 previously finishing cases stop. Net improvement does not
erase those losses. Rank 16 has a larger first-step gain under these settings;
we still need the full trajectories and later independently generated practice.

Rank 1 uses the repaired native training executable, while the other rank arms
retain their original native hashes. The shared inference runtime and frozen
cases match; backend provenance remains explicit. The fix is credited to
**edenfunf's [llama.cpp PR #30142](https://github.com/ggml-org/llama.cpp/pull/30142)**,
commit fdb4a0553f6ecb00450f04cc8da5b2b38dd9146d, and the
[PCC draft integration](https://github.com/CC-David-CC/Private_Context_COW/pull/1).
The earlier broader matrix-gradient numerical failures remain unresolved.

[Full snapshot and continuation receipts](../validation/lora-rank-extension-20261025-bh/README.md)
were captured at 2026-10-25T20:32:01Z. The original five-series graph stays separate.
