# Native MiniCPM: first attached-LoRA learning

The current [combined learning/forgetting graph](COW-SHARED-ROOT-LEARNING.md)
now includes 15 complete attached-LoRA checkpoints: update 15 scored 396/864,
with 346 original wrong answers gained and nine original correct answers lost.
This remains development evidence, without promotion or merged-deployment qualification.
[Latest direct curve data](../validation/minicpm-native-learning-20261024/direct-lora-learning-ax.json).
The earlier six-point snapshot below is retained.

The directly attached rank-16 LoRA hat reaches **298 correct answers out of 864**
after six updates and 162 practice presentations, from the original model's 59.
This is the separately labelled direct-hat curve, with its original adapter and
optimizer state continued exactly. The original merged-deployment parity gate
remains failed at its unchanged bounds.

| Native LoRA updates | Practice presentations | Correct / 864 | Naturally finished / 864 | Answers gained vs original | Original successes lost |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 0 | 59 | 415 | 0 | 0 |
| 1 | 27 | 154 | 631 | 95 | 0 |
| 2 | 54 | 209 | 762 | 151 | 1 |
| 3 | 81 | 231 | 781 | 173 | 1 |
| 4 | 108 | 255 | 793 | 197 | 1 |
| 5 | 135 | 282 | 823 | 224 | 1 |
| 6 | 162 | 298 | 853 | 243 | 4 |

The [combined early graph](COW-SHARED-ROOT-LEARNING.md) shows this attached-hat
series alongside the full-weight settings. The original and trained execution
controls matched every sampled token on all 864 questions; their two runtime
identities remain explicit in the artifacts. This is a comparison of the
predeclared settings, with different rates/capacity, rather than a claim of an
optimal optimizer or adapter size.

## Learning and forgetting remain separate

At update 3, 173 previously wrong answers become correct and one original
success becomes wrong. All originally finishing responses finish again, along
with 366 additional cases. Between updates 1 and 2, the model gains 59 answers
and loses four; between updates 2 and 3, it gains 23 and loses one. Newly learned
answers can therefore be lost even when they were not among the original 59.
By update 6, the original-baseline count is 243 gains and four losses.
The artifact includes both original-baseline and consecutive-update comparisons.

These exploratory checkpoints are retained while the controlled 68-update recipe
continues. The frozen nonregression eligibility policy still refuses promotion
when a prior success is lost. That receipt does not discard the checkpoint or
stop this exploratory trajectory. Later practice can address a failure family
with fresh verified variants and mixed review; these development answers do not
become practice examples. Sealed acceptance and broader tool/admin/research
behavior remain unfinished.

This comparison begins from the original MiniCPM. The earlier AnswerStop01 model
and its [completed quantization study](MINICPM-QUANTIZATION-RESULTS.md) remain
separate preserved artifacts.

## Native mechanics and work

Update 2 has 590 finite, nonzero adapter-gradient groups. Its batch loss changes
from 2.96278 to 1.63270; an independent reload differs by 1.67e-7, within PCC's
unchanged 2e-4 bound. That native update plus reload allocated 83.6 seconds on a
shared A100. Per-batch losses describe that batch, not a fixed validation loss
curve. No PyTorch path or new training seed was used.

Consumed forward tokens in the complete COW panel fall from 99,437 originally
to 86,504, 77,417 and 76,399 across these three hats. Stopping improvements reduce
how much decode work the panel performs. Token counts are not an elapsed-time or
FLOP speedup: the adapter adds operations and the A100 has other shared loads.

The native bridge and fresh oracle binaries are byte-identical before and after
the new immutable-hat wiring. Original F16, original F32 and the earlier F32 COW
baseline match every sampled sequence on all 864 questions. The same is true
when the saved full-weight AdamW update-8 model is reassessed through the new
runtime (385 correct, 855 finished). These are observed controls on those two
models, not an all-context numerical certification. See [PCC's attached-hat
qualification](https://github.com/CC-David-CC/Private_Context_COW/blob/feat/native-learning-curves-20261024/docs/DENSE-LORA-COW.md).

## Input separation and reproducible reporting

An exact-input audit of 864 practice examples against 864 development cases found
zero identical rendered user questions and zero identical supervised prefixes.
The recorded training/example ID strings also did not overlap; ID namespaces
alone do not establish independence. Exact equality checks do not prove semantic
disjointness, broad generalization or sealed acceptance. The frozen practice
stream has not changed.

[Aggregate learning, per-skill changes, native mechanics and control identities](../validation/minicpm-native-learning-20261024/direct-lora-learning-aq.json)
contain no private question/answer text or model files.

An agent or person can reproduce the report with the existing result files:

```sh
python3 scripts/report_direct_lora.py --input /private/collected-results --output curve.json
python3 scripts/plot_shared_learning.py --lora-data validation/minicpm-native-learning-20261024/direct-lora-learning-aq.json
```

The report input has a `baseline` directory and `update-NNN` directories, each
with complete `result.json` and `settlement.json` files. Optional original
`mechanics-private.json`, baseline controls, trained-runtime bridge and overlap
audit receipts are checked and reduced to shareable evidence. Paired results
carry PCC's actual base-plus-adapter identity. Native provenance and retention
remain PCC/owner responsibilities; the reporter grants no GPU, trains no model,
deletes no candidate and authorizes no promotion.
