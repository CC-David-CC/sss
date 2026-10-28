# CUDA size-one outer-product qualification checkpoint

The [summary](summary.json) records our local control and patched checks.
We reproduced the cuBLAS leading-dimension crash with upstream CUDA code and
passed 103/103 CPU-reference operator cases after applying **edenfunf**'s
[llama.cpp PR #30142](https://github.com/ggml-org/llama.cpp/pull/30142), commit
`fdb4a0553f6ecb00450f04cc8da5b2b38dd9146d`. Those are our RTX4090 observations,
separate from the author's reported tests. The pinned upstream base was
`6050b467c07a95c7b87debd4ddac2f8ba8d9b807`.

The larger matrix checker remains unresolved: its default-precision invocation
reported 31 failures; disabling TF32 reported 7 failures. Thresholds were
unchanged and both original logs are retained privately with their hashes.
Reported totals include skipped/unsupported configurations. Repeated operator
runs can draw different inputs, so these counts alone do not isolate a cause.
Do not describe this checkpoint as an overall numerical qualification pass.

The operator result does not establish actual MiniCPM rank-one update, reload,
optimizer continuation, COW inference or model quality. The A100 uses a separately
built dependency at the study's original pin with its existing F32 patches plus
the credited import. Original live study libraries are untouched. HIP/SYCL are
not claimed tested. See the [rank-study extension](../../docs/LORA-RANK-EXTENSION.md)
for matched practice and evaluation requirements.
