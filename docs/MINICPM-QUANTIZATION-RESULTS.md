# Does the learned behavior survive smaller model files?

The completed FP16, Q8 and Q4 comparisons retain most or all of the trained
model's aggregate score on this frozen math/state development set. The trained
FP32 checkpoint scores 482/864; FP16 scores 481, Q8 scores 482 and Q4 scores 467.
All four trained variants finish every response naturally. These are measured
full assessments, not estimates from model size or a few selected examples.

| Stored precision | Original correct | Trained correct | Original finished | Trained finished | Trained file size |
| --- | ---: | ---: | ---: | ---: | ---: |
| FP32 | 59/864 | 482/864 | 415/864 | 864/864 | 10,072,171,584 bytes |
| FP16 | 59/864 | 481/864 | 415/864 | 864/864 | 5,039,006,784 bytes |
| Q8_0 | 41/864 | 482/864 | 392/864 | 864/864 | 2,679,710,784 bytes |
| Q5_K_M | unmeasured | unmeasured | unmeasured | unmeasured | not reported yet |
| Q4_K_M | 37/864 | 467/864 | 534/864 | 864/864 | 1,561,318,464 bytes |
| Q3_K_M | unmeasured | unmeasured | unmeasured | unmeasured | not reported yet |
| Q2_K | unmeasured | unmeasured | unmeasured | unmeasured | not reported yet |
| Q1_0 | unmeasured | unmeasured | unmeasured | unmeasured | not reported yet |

The trained FP16 model gains **one** answer and loses **two** relative to its FP32
parent. Its net gain over the original same-format model is 422 answers, versus
423 in FP32. That retains about 99.8% of this measured net score improvement
while roughly halving file size. This is a ratio on this development set, not a
claim that 99.8% of general intelligence survives conversion. FP16 also loses
12 original successes while gaining 434 previously wrong answers; those losses
remain visible for later mixed practice.

Q8 keeps the FP32 total of 482, but it gains two answers and loses two other
answers relative to FP32. Equal totals do not mean identical behavior. Q4 gains
19 and loses 34 relative to FP32, a net loss of 15 answers; it retains about
96.9% of the FP32 correct-answer total in about 15.5% of its file size. Against
the original Q4 artifact, trained Q4 gains 435 answers and loses five, with 330
additional natural completions and no lost completions. Its score is 467 versus
37 on the same quant format. Smaller formats are not assumed to monotonically
reduce quality. These paired changes are observations on this sample.

Original FP16 and FP32 have identical Boolean correctness/completion outcomes
on every case. The trained FP32 score on this RTX 4090 also reproduces the
earlier 482/864 with 864 completions on the RTX PRO 6000. These observations
do not promise identical floating-point logits or every future result across
hardware. The within-table comparisons use one pinned runtime and one GPU.

## What was held fixed

The original and trained variants use the same 864 questions, exact-answer
checker, tokenizer, prompt renderer, native runtime and decoding limits. There
are nine math/state leaves, each with independent, composition and
transfer/recovery gates. Decoding is greedy, thinking is closed in the qualified
template, input context and batch are 512 tokens, and generation is capped at
64 tokens with assistant ending IDs 1 and 130073. No evaluation answers enter
training. The trained source is the historical AnswerStop-01 checkpoint, not a
new update trained during this quantization study.

The oracle recomputes the complete prefix at each generated token. This is a
correctness experiment; its wall times are not production cached-serving
throughput. Conversion uses the pinned llama.cpp-derived quantizer through PCC's
existing model tooling. No new quantization engine or training framework is
introduced. All model binaries remain private on fleet machines.

The trained FP32 run's maximum sampled process memory was 9,288 MiB; FP16's was
6,016 MiB, Q8's 3,036 MiB and Q4's 2,100 MiB. These are one-second `nvidia-smi` process samples, not guaranteed
instantaneous peaks or training VRAM estimates. Model format, runtime buffers
and execution shape all contribute to memory use.

## Repeat the report

The live inference runner writes immutable `FAMILY-FORMAT-summary.json` and
`FAMILY-FORMAT/result.json` files. After a row completes, an agent or person can
regenerate the aggregate without invoking a model:

```sh
python -m sss_integration.quantization_report \
  --directory /path/to/owned-evaluation-matrix \
  --formats F32 F16 Q8_0 Q5_K_M Q4_K_M Q3_K_M Q2_K Q1_0 \
  --output quantization-progress.json
```

The output path must be new. The report checks complete unique case outcomes,
reconciles totals and model identities, and refuses comparisons with changed
runtime, questions or skill/gate assignments. It computes paired gains/losses
against each family's FP32 control and against the original at the same format.
Missing rows stay unmeasured; recorded failures are labeled infrastructure
incomplete and never become zero model scores. It
exports aggregate counts, skill/gate changes and evidence hashes, without answer
text or per-case outcome lists. It does not change an acceptance policy,
promote a model, execute training, or upload weights.

[Measured aggregate and source hashes](../validation/minicpm-native-learning-20261024/quantization-progress.json),
[report checks](../validation/minicpm-native-learning-20261024/quantization-report-checks.json).
Run the focused checks with:

```sh
python -m unittest sss_tests.test_quantization sss_tests.test_paired sss_tests.test_paired_rates -v
```

Q5, Q3, Q2 and Q1 comparisons remain unfinished. Their behavior may improve or
degrade; no monotonic relationship with bit count is assumed. Repeated feedback
on this development set also does not replace sealed qualification or tests of
coding, Linux administration, tool use, research and long-context retention.
