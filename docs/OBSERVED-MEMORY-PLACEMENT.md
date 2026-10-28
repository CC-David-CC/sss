# Use measured memory to find useful GPU windows

The precision evaluator had waited for 24 GiB free on a shared A100, even for
small quantized models. Original process-bound NVML observations show why that
blanket gate wasted available windows. On the completed rank-16 sweep, the
observed process peaks were:

| Format | Peak observed MiB | Samples |
| --- | ---: | ---: |
| F32 | 9,326 | 42 |
| F16 | 6,056 | 50 |
| Q8_0 | 3,080 | 37 |
| Q5_K_M | 2,350 | 39 |
| Q4_K_M | 2,144 | 39 |
| Q3_K_M | 1,922 | 46 |
| Q2_K | 1,708 | 50 |
| Q1_0 | 1,278 | 95 |

These are samples of actual process usage, not proven upper bounds. They apply
to this dense MiniCPM geometry, stored format, COW runtime, frozen 864-case
evaluation, 512-token context/batch and 64-output-token limit. They are not
training-memory estimates. Backprop and optimizer state need separate evidence.

The new rank-4 sweep uses the existing converted artifacts and a matching-layout
forecast to consider smaller windows. Its initial placements used GPU 1 with
21,974 MiB free for F32, GPU 2 with 14,659 MiB free for F16, and GPU 4 with
13,260 MiB free for Q8. The previous 24-GiB gate would have excluded all three.
Each format keeps its own claim and result. The reference and quantized formats
can evaluate independently; paired comparisons wait for complete F32 evidence.

## S³ supplies analysis; PCC retains execution authority

`sss.studies.memory_forecast.observed_memory_forecast` consumes an explicit
workload descriptor, original process identity, memory samples and an evidence
hash. `placement_candidates` refuses changed runtimes, model tensor layouts,
hardware classes, formats, evaluations or context/output bounds. It also rejects
process-ID reuse, malformed memory values and changed forecast records.

Busy GPUs remain eligible. Candidate ordering prefers idle compute, then the
smaller fitting window. There is no 50-percent utilization exclusion and no
universal 24/54/70-GiB floor in this selector.

The forecast starts no process, acquires no GPU lease and grants no permission.
The operator still uses PCC's existing lease, rechecks current free memory and
preserves any allocation failure as infrastructure evidence. Its
`work_authorized: false` field means a measurement is not an authorization source;
it adds no confirmation step to work the owner has already approved.

The optional owner adapter derives the layout using PCC's actual GGUF reader,
including tensor names, shapes, storage types, dense geometry and vocabulary
size. For the frozen study it validates the original evaluation intent against
the installed source hashes, runtime libraries, tokenizer, case input bytes,
shared prefix and policy before reusing an observed forecast. Changing weights
with the same layout can reuse that bounded observation; changing the workload
requires a new matching measurement or a native memory plan.

## Preserve failed preflights and completed work

The first rank-4 launch encountered an unavailable helper in the older frozen
evaluator before any model evaluation began. All seven CPU conversions had
completed. The corrected preflight read the actual installed runtime evidence,
verified every converted artifact, and proved that no original evaluation had
started. It reused those files under a new controller identity and preserved
all original failures. It did not repeat a training update or completed question.

The existing resource-budget API retained the old unknown-allocation charges and
recorded separate, evidence-bound zero-GPU reconciliations for the failed
preflights. CPU conversion work is not reported as GPU inference time.

Eleven pure CPU controls cover matching workloads, process reuse, precision and
context changes, busy-card eligibility, hardware mismatch, malformed telemetry
and changed forecasts. An additional eight-format installed preflight validated
the actual model layouts and runtime without starting model work. The
[sanitized receipt](../validation/learning-program-20261024/observed-memory-placement-20261026.json)
retains the source identities and observation counts.

This is placement evidence, not an inference speed benchmark, model-quality
claim, or proof that a sampled peak is sufficient for every later request.
Original evaluations and existing live training workers retain their own frozen
configurations; this change does not silently move or restart them.
