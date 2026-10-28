# BW-to-S³-to-PCC CPU proof (2026-10-28)

This controlled machinery test created a BW failure capture for `python.double`,
created its corrected capture, rechecked both captured source files with S³, and
selected the distinct `python.triple.practice` example for `code.python.debug`.
S³ independently checked the practice reference before creating its immutable
lesson archive. PCC stored that lesson and the native training request used exactly
the S³ token sequence, targets, and 32-token answer-only loss mask.

One PCC full-weight CPU update completed. The generated fixture's loss moved from
5.67208 to 5.66749. The original fixture remained unchanged, and the candidate was
not promoted. It is a tiny byte-vocabulary fixture, not MiniCPM or another language
model; the loss change proves execution only. This test does not show learned skill,
transfer, retention, or a real model failure.

Machine: llm-79, AMD Ryzen 7 2700, CPU only. PCC source: `d4defb8e`; BW source:
`afa28395`; native executable SHA-256:
`76b165958f59187796c3c9d5bb277ad4fe51ac6659bc876dc0b1f37910c8be9a`. The native
build used llama.cpp commit `972d2313bc0bf0a45f634f77d95c9fb03aeab12c`. The exact
sanitized receipt and candidate/base hashes are in `result.json`. Captured source
files and the generated candidate remain outside the repository.

The script is `sss_integration/bw_practice_native_cpu.py`. On an authorized Linux
host with matching checkouts and the PCC native executable, run:

```sh
BW_ROOT=/path/to/bw PYTHONPATH=/path/to/sss:/path/to/bw:/path/to/pcc \
python3 /path/to/sss/sss_integration/bw_practice_native_cpu.py \
  --pcc-root /path/to/pcc --bw-root /path/to/bw \
  --native-executable /path/to/pcc-native-train \
  --workdir /new/private/output/directory
```

The work directory must not already exist. The run is CPU-only and writes a private
candidate there; it never promotes it.
