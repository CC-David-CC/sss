# How much learned behavior survives a smaller GGUF?

[Compare all ten original endpoint precision sweeps](FINAL-CHECKPOINT-PRECISION.md) (all 80 panels complete).

This is a completed precision sweep of the completed **AdamW LoRA rank-16,
update-68** checkpoint. It is separate from the unfinished optimizer/rank
comparison. The same 864 frozen arithmetic/state questions are used throughout.
All eight formats, including the F32 reference, are complete (26 October 2026).

![Rank-16 precision sweep](results/minicpm-20261026/rank16-final-precision.png)

The **orange dashed line** shows the original, untrained model's measured score
at each quant size. The **gray dotted line** marks its F16 reference: 59 correct
and 415 naturally finished out of 864. Original F32 is now included after auditing all 864 existing response receipts; it also scored 59 correct and 415 naturally finished. No inference was repeated. The original sweep used a different runtime; this is
a historical comparison on the same frozen cases, not a matched-runtime estimate
of the effect of training alone. See the [original receipts and scores](MINICPM-QUANTIZATION-PROGRESS.md).
The [overlay validation](results/minicpm-20261026/original-overlay-validation.json)
records both runtime identities, source hashes and the recovered original F32 point.

| Format | Original correct / 864 | Trained rank-16 correct / 864 | Difference in total |
| --- | ---: | ---: | ---: |
| F32 | 59 | 494 | +435 |
| F16 | 59 | 494 | +435 |
| Q8_0 | 43 | 491 | +448 |
| Q5_K_M | 58 | 482 | +424 |
| Q4_K_M | 34 | 492 | +458 |
| Q3_K_M | 50 | 401 | +351 |
| Q2_K | 4 | 36 | +32 |
| Q1_0 | 0 | 0 | 0 |

The table below retains the within-trained-checkpoint, paired comparison to F32.

| Format | GGUF GiB | Correct / 864 | Natural finishes / 864 | Newly correct vs F32 | Previously correct lost |
| --- | ---: | ---: | ---: | ---: | ---: |
| F32 | 9.380 | 494 | 864 | 0 | 0 |
| F16 | 4.693 | 494 | 864 | 0 | 0 |
| Q8_0 | 2.496 | 491 | 864 | 0 | 3 |
| Q5_K_M | 1.684 | 482 | 864 | 10 | 22 |
| Q4_K_M | 1.454 | 492 | 864 | 20 | 22 |
| Q3_K_M | 1.203 | 401 | 863 | 20 | 113 |
| Q2_K | 0.969 | 36 | 817 | 8 | 466 |
| Q1_0 | 0.504 | 0 | 0 | 0 | 494 |

Every row comes from a complete 864-case assessment. Q1's zeros are measured results, not placeholders. The
[CSV](results/minicpm-20261026/rank16-final-precision.csv),
[receipt hashes and skill/gate counts](results/minicpm-20261026/rank16-final-precision.json)
and [plot source](results/minicpm-20261026/plot_rank16_precision.py) are retained.
Raw protected responses and all model weights remain private.

## ELI5

We packed the same trained model into smaller files and asked it the same
questions. F16 kept every F32 answer/finish verdict. Q4's total is almost the
same as F32, but it gained 20 correct answers and lost 22 others. A similar total
does not mean it remembered exactly the same things. Q3 fell to 401/864, so the observed sharp drop starts below Q4 in this
sweep. Q2 scored 36/864 and naturally finished 817 responses. Q1 scored zero and none of its responses reached a natural finish within the 64-output-token limit. The curve has a dip at Q5 and a
recovery at Q4.

## Master's level

The F32 master is a native merge of the existing rank-16 adapter at 68 updates
(1,836 ordered training presentations). Every saved weight passed the independent
FP64 merge audit. Its 864 answer/finish verdicts match the attached adapter's
original assessment; the attached and merged execution paths have different
runtime identities. This is behavioral agreement on this panel, not all-position
logit equivalence or identical generated text.

Every quant is converted directly from that F32 master through the pinned
native quantizer. Tensor names/shapes and model/tokenizer metadata are checked;
each file receives a new immutable weight identity. The precision sweep uses
the same standalone COW runtime, shared-prefix evaluation, frozen case IDs,
greedy decoding, 512-token context and 64-output-token limit. Q5 and Q4 are
mixed K-quant formats, not a claim that every tensor is stored at exactly five
or four bits. File sizes are disk sizes, not total serving VRAM requirements.

Q4 has a net loss of two answers, with 42 changed correctness verdicts. This
is why S3 records paired gains/losses and skill/gate groups rather than using
only aggregate accuracy. F16 has zero correctness or completion losses in this
panel; Q8 loses three answers and gains none.

## PhD level

This is one trained checkpoint under one specified evaluation protocol. It does
not establish a universal quantization threshold, a general ordering of formats,
a mechanism for Q4's additional passes, or superiority of its parent optimizer.
Near-equal totals cannot establish behavioral equivalence. Cases share generated
families; treating every response as an independent sample would overstate what
these development measurements establish. No seed-repeat experiment ran.

The earlier failed attached-versus-merged all-position logit gate remains in its
original record. Saved-weight arithmetic, per-case behavioral retention and
release qualification answer different questions. These results neither erase
that failure nor promote any model. The complete 68-update
comparison, broader skill/workflow coverage and sealed acceptance remain open.

## Applied reading

The current Q4 file is about 1.454 GiB, compared with about 9.380 GiB for F32.
It retains nearly the same total score here while changing which questions pass.
Inspect the per-domain losses before choosing a format for a particular job.
F32 through Q4 naturally finished all 864 responses; Q3 finished 863. Q2 naturally finished 817 responses; Q1 finished none within the configured output limit. Later QAT experiments remain separate.

These measurements ran on shared A100 GPUs. Recorded allocation times include
contention and storage work, so they are not isolated inference speed benchmarks.
No training was repeated to produce this sweep. No GGUF has been uploaded or
accepted for release. This completed sweep is separate from the other arms, which remain in progress.
