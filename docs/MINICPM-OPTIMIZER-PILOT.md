# MiniCPM native optimizer pilot — 2026-10-24

This pilot exercises real full-weight MiniCPM5-2B training, saved-candidate
reload and completed optimizer continuation. PCC owns native C++/GGML forward,
ordinary backprop, updates and immutable artifacts. S³ supplies independently
checked practice, separates protected checks and records the outcome. BW does
not need to run to exercise this integration. No PyTorch is used.

The results below are mechanics evidence. They do not establish better answers,
preserved capabilities or a winner between optimizers. No candidate is promoted.

## Measured results

All planned gates passed on one RTX PRO 6000 Blackwell, using the same pinned
native F32 binary. The longest-example probe covered all 381 parameter tensors
with finite nonzero gradients and wrote no candidate. The public probe command
was also exercised successfully against the real model without an update.

| Run | Examples in this run | Global step after run | Reload-loss error | Optimizer-only seconds/update | Allocated seconds |
| --- | ---: | ---: | ---: | ---: | ---: |
| Fresh Muon | 2 | 1 | 1.19e-7 | 2.623 | 127.0 |
| Resumed Muon | 1 | 2 | 0 | 2.630 | 181.8 |
| Uninterrupted Muon | 3 | 2 | 0 | 2.631, 2.632 | 128.5 |
| Fresh AdamW control | 2 | 1 | 5.96e-8 | 0.061 | 156.8 |

Every update covered all 381 parameter tensors with nonzero gradients. Muon
handled 294 hidden matrices; auxiliary AdamW handled the other 87 tensors.
The standalone AdamW control handled all 381.

**Completed continuation is bit-exact here:** all 381 weight tensors and 468
moment tensors match, covering 5,568,460,800 scalar values, with zero differing
bits and zero tolerance failures. This is one model/data/build/backend profile,
not a promise of identical training across hardware. GGUF/state file hashes
differ because their lineage headers differ; the actual parameter/moment arrays
match. The comparison did not widen its predeclared tolerances.

Practice loss on the first two examples changed from 7.9423 to 4.9216 for Muon
and to 2.4303 for AdamW. The remaining example changed from 1.1531 to 0.7917 on
the second Muon step. These are losses on trained batches, not independent
behavior scores or a tuned optimizer ranking.

Muon used about 39.4% less optimizer-state storage, but its optimizer computation
was about 43 times slower than AdamW on this small-batch workload. Loading,
backpropagation, candidate evaluation, exporting and hashing are outside that
optimizer-only timer. Allocated run time includes the broader owned resource
window and substantial checkpoint I/O; it cannot be used as a clean compute
comparison. The real question remains quality and retention per fixed compute
budget, including whether a larger batch amortizes optimizer cost.

The four training runs and two no-update probes used **0.16943 single-Blackwell
GPU allocation-hours**, about 10.17 minutes. No A100 job ran in this pilot. The
full-state comparison ran on CPU outside the GPU allocation window. All owned
GPU work is settled. Core S³ tests: 122 passed; optional comparator checks: 3
passed. [Machine-readable results, hashes and complete comparison](../validation/learning-program-20261024/minicpm-optimizer-real-pilot.json).

## Practice and identities

The frozen S³ pack closes addition-with-carry and subtraction-with-borrow over
five prerequisite-connected arithmetic skills. It admits 30 practice lessons
and retains 30 separate development/blind checks. Only three explicitly selected
practice examples reach the training worker:

| Skill and gate | Consumed input tokens | Selected answer targets |
| --- | ---: | ---: |
| Addition with carry, independent | 59 | 3 |
| Subtraction with borrow, composition | 73 | 3 |
| Place value, transfer/recovery | 120 | 14 |

These are owned synthetic demonstrations, not observed MiniCPM failures. The
answers pass the existing independent S³ checkers. Actual PCC admission,
MiniCPM rendering/tokenization and explicit next-token loss masks are used.
Thinking is disabled and only checked answers are selected; this pilot does not
qualify thinking-token training. Protected questions/answers are not transferred
to the training worker or included in the published practice TXT.

[The practice TXT](../examples/finished-training-examples/minicpm-optimizer-pilot/practice.txt)
and its manifest preserve the requested finished-example artifacts and exact
selection identities. The original F16 model remains unchanged; generated
full-weight candidates and optimizer states remain on the training host.

## What the gate measures

1. Probe the longest selected example before updating. Require finite complete
   parameter-gradient coverage and confirm that no candidate was written.
2. Run one Muon update on the first batch of two examples. Export a separate F32
   candidate and completed optimizer state. Reload the candidate in a fresh
   native process and check the same batch's post-update loss.
3. Resume from the exact candidate/state/data cursor for the remaining example.
   Preserve the global optimizer step and all moments.
4. Start from the same original model and run those two batches uninterrupted.
   Compare every candidate weight and optimizer moment with the resumed result.
5. Exercise an independent fresh AdamW control through the same update/export/
   reload machinery. This one-step mechanics control is not a learning trial.

The frozen Muon rate is 5e-5 with auxiliary AdamW at 1e-6, momentum .95,
Nesterov, five Jordan-quintic iterations, original shape scaling and zero decay.
Hidden Q/K/V, attention-output and FFN matrices use Muon; embeddings, prediction
head and normalization/other auxiliary parameters use AdamW. The fresh AdamW
control uses rate 1e-6. These rates are explicit pilot settings, not tuned model
recommendations. RMS-scaled and fast-refine variants remain separate learning
experiments; their tiny-model mechanics are qualified in the PCC checkpoint.

Both continuation tolerances were frozen before any update: absolute 2e-7 and
relative 2e-6, using the larger magnitude of each compared pair. Report exact
bit differences as well. A matching training loss or whole-file SHA is not a
substitute: lineage metadata can change a GGUF SHA without changing its weights.
The reload-loss error limit is 2e-4; it is not a universal hardware tolerance.

## Reproduce with owned resources

Use matching S³/PCC sources, the qualified native training binary and a local
F16/F32 ordinary-Llama model. MiniCPM requires its qualified tokenizer/renderer.
The current pilot step's gradient gate explicitly expects 381 parameter tensors;
another architecture needs its own gate and qualification. The native training
profile is bounded to 512 input positions and 256 selected targets. This does
not exercise the model's 128K inference context or extended RoPE/YaRN.

From the S³ source checkout, prepare data without a training runner:

```sh
python -m sss_integration.optimizer_pilot_prepare \
  --pcc-root /source/pcc --model /models/MiniCPM5-2B-F16.gguf \
  --model-contract-id EXACT_QUALIFIED_MODEL_CONTRACT_ID \
  --output /private/new-preparation
```

Run the gradient-only command with the qualified build and explicit resources:

```sh
python -m sss_integration.native_optimizer_probe \
  --pcc-root /source/pcc \
  --selection /private/new-preparation/prepared/selection-private.json \
  --model /models/MiniCPM5-2B-F16.gguf \
  --native-executable /build/pcc-native-train \
  --output /private/gradient-probe \
  --gpu-index OWNED_PHYSICAL_INDEX --device-budget-gib EXPLICIT_BUDGET
```

It selects the longest checked practice example, pins the model/binary and
checks every GGUF parameter name against the returned finite, nonzero gradients.
It preserves the native request, result, physical GPU admission and allocation
settlement. A candidate file or a claimed update fails the probe. This result
is a gate input, not an authority grant: only the operator configures executable,
device and resources. For this MiniCPM selection the result must report 381
finite gradients. The preparation and probe do not update weights.

Then run one owned resource window with a **new** output directory:

```sh
python -m sss_integration.native_optimizer_step \
  --pcc-root /source/pcc \
  --selection /private/new-preparation/prepared/selection-private.json \
  --gradient-evidence /private/gradient-probe/result.json \
  --model /models/MiniCPM5-2B-F16.gguf \
  --native-executable /build/pcc-native-train \
  --output /private/muon-first --optimizer muon \
  --learning-rate 0.00005 --steps 1 --batch-size 2 \
  --gpu-index OWNED_PHYSICAL_INDEX --device-budget-gib EXPLICIT_BUDGET
```

The command checks data identities, disk reserve and fresh GPU headroom/use,
holds the physical GPU lease, delegates the update to PCC and checks candidate
reload in a fresh native process. It records the exact request, executable/source
hashes, candidate/state identities, counters and allocated resource time.
`--parent-result /private/muon-first/result-private.json` resumes a completed
result in another new output directory. Keep the original data, settings and
rate. A fresh two-step run has no parent and uses `--steps 2`. The AdamW control
uses a new directory, `--optimizer adamw --learning-rate 0.000001`.

Inspect the original PID/start ticks, native launch and result after an
interruption. Never rerun solely because an observation timed out. These states
cover completed updates; mid-step transactional recovery is not qualified.

Compare the completed resumed and uninterrupted results on a host with NumPy:

```sh
python -m sss_integration.native_optimizer_compare \
  --pcc-root /source/pcc \
  --left-result /private/muon-resumed/result-private.json \
  --right-result /private/muon-uninterrupted/result-private.json \
  --atol 0.0000002 --rtol 0.000002 --output /private/continuation-comparison.json
```

The comparison validates result identities, artifact hashes, candidate/state
binding, complete tensor layouts, configuration, data order, step and cursor.
It streams every weight and moment, checks finite values and reports both exact
differences and tolerance failures. It does not require whole-model RAM copies.

## Resource implications and next gate

The original model is about 5 GB, but its saved F32 parameters occupy about
10.07 GB. Muon state occupies about 12.21 GB, versus AdamW's 20.13 GB. Three
Muon checkpoints plus one AdamW checkpoint consume about 90 GiB, before the
explicit 16 GiB disk reserve and small metadata/logs. A model download size is
not a training disk or VRAM budget. Per-device admission includes persistent
weights, gradients, moments, reserve and graph allocation checks.

The learning study still needs a frozen mixed-practice dose, equal allocated
compute budgets, baseline/candidate behavioral evaluation, per-domain retention
and actual accept/reject evidence. More optimizer steps or lower practice loss
alone cannot pass that gate. Short development checks do not replace the planned
96-question domain assessments. Standard Muon, RMS scaling and the defined
fast-to-refine schedule must be compared as distinct configurations; broad AdamW
ablations remain stretch work. BW's separate shell verification/termination
failure must retain its own harness attribution and evidence.
