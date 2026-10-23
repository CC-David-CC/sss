# Models, measurements and what the numbers mean

S³ owns the full methodology and result history. [PCC](https://github.com/CC-David-CC/Private_Context_COW)
summarizes model downloads, hardware and serving evidence.
[BranchWrite](https://github.com/CC-David-CC/BranchWrite) summarizes the practical
task implications. The same result should be linked from both, with one detailed
report here, rather than maintained as three independent sets of numbers.

## Model identities

Sizes are downloaded weight bytes, not required VRAM or total installation space.
GB is decimal; GiB uses 1,073,741,824 bytes.

| Model | Weight download | Identity and role |
| --- | --- | --- |
| Qwen3.8 Flash UD-Q4_K_XL | 111,334,654,784 bytes; 111.33 GB / 103.69 GiB | PCC's pinned default Flash shards; expert packing and runtime caches need additional disk space. |
| Wen 1 BF16 | 15,942,827,584 bytes; 15.94 GB / 14.85 GiB | Historical original, SHA-256 `40f048a00bc2a2a8c2db163999f0af90613d136376e9b3c9372457b1769b44ca`. |
| Wen 1.1 BF16 | 16,244,817,856 bytes; 16.24 GB / 15.13 GiB | Current HF download, SHA-256 `49425fd802b04b400a1725e8afe527c405bb15e828d0275ff295e38396839f34`. |

The [Wen repository](https://huggingface.co/davidflanagancomm/Wen) currently exposes
1.1. Original Wen 1 remains available at revision
`674907f2b65baa576e678b9c9a06bf07c3db9076`; 1.1 is pinned at
`7328e9fab25b207523b5236aa29c81be24eed924`. Both cached evaluation files match
their published SHA-256 values. The separate [PCC download guide](https://github.com/CC-David-CC/Private_Context_COW/blob/main/docs/MODELS-AND-RESULTS.md)
gives commands and the supported dense-adapter route.

Wen 1.1 came from a tiny nine-example, four-update, rank-eight LoRA experiment.
Its merged file keeps most tensors BF16 and stores three changed final-MLP
matrices as F32, accounting for the larger download. The earlier 19-case pilot
gave **15/19 for both models with the same four failures**. The merge also
matched the adapter's 132 checked next-token choices, including a long-prefix
continuation, with maximum observed logit difference about 6.2e-6. That is
merge/mechanics evidence, not a demonstrated improvement in general usefulness.

## Historical Flash on llm-60: retained evidence

These are existing measurements on an RTX PRO 6000 Blackwell 96 GB with FP16 KV,
not a new run or a current reservation of that machine. The context-pressure
campaign deliberately used a 9 GiB RAM cache pool. Its ordinary setup used larger
RAM/disk budgets. Do not treat these short trials as a day of inference load.

| Measurement | Q4 | Q8 | Scope |
| --- | --- | --- | --- |
| Native generated IDs / saved full-logit vectors | 768 / 12 | 768 / 12 | Each compared with independent references; maximum observed error zero. |
| Continued output after disk restore | 128 tokens | 128 tokens | Six positive evictions and one disk reload per quant; zero saved-prefix prefill. |
| Median generation-only speed | 74.63 tokens/s | 62.29 tokens/s | Six distinct short questions per model. |
| Median output / whole-request time | 33.20 tokens/s | 28.35 tokens/s | Includes question prefill, capture and durable publication. |
| One measured 128-token disk-return request | 4.606 s | 6.018 s | One request each; excludes startup and base preparation. |

Q4 also passed three concurrent client submissions with serialized use of one
worker and unchanged source states. Restart, disconnect and retry harnesses
passed their lifecycle checks; those lifecycle runs did not compare logits.
See [the source campaign and linked evidence](https://github.com/CC-David-CC/Private_Context_COW/blob/main/docs/context-cow/CONTEXT-COW-GUIDE.md).

A separate Q8 stream study used an 8,192-token synthetic prefix, 512-token
suffix and 128 outputs, one excluded warm-up pair and three measured repetitions
per branch. Resident median first-token time was 0.696 s, median received gap
22.82 ms, steady received rate 44.44 tokens/s and durable-completion rate
30.71 tokens/s. It used same-host subprocess receipt, not network HTTP timing.
The disk study's six repetitions gave 1.449 s first-token time, 44.47 steady
tokens/s and 26.00 durable tokens/s; filesystem warmth was uncontrolled.
These rates use different timing boundaries from generation-only speed above.
See [the timing definitions and artifacts](https://github.com/CC-David-CC/Private_Context_COW/blob/main/docs/context-cow/CLIENT_STREAM_MEASUREMENT.md).

IQ3_XXS and IQ2_XS were inventoried on llm-60 but **not qualified there**. File
presence is not a benchmark. Separate trials on the RTX 4090/32 GB RAM setup
reported IQ3 short-branch received rates 7.52/11.31 tokens/s and IQ2
11.96/20.18 tokens/s; longer IQ2 branches gave 9.13/13.21 tokens/s. These are
different workloads and hardware. Coding attempts included a timeout and a RAM
reservation failure, and recovery remained unresolved. There was no new numerical
oracle qualification. See [that bounded campaign](https://github.com/CC-David-CC/Private_Context_COW/tree/main/validation/lower-quants-llm49-20261021).

There is no complete same-suite Q4/Q8/IQ3/IQ2/Wen leaderboard yet. Historical
serving speed cannot stand in for tool-use, coding or administration quality.

## Wen on the current S³ tasks

The completed first paired trial ran **Wen 1, then Wen 1.1**, on the same
A100-SXM4-80GB, nine original fixtures, native adapter, prompt, case order and
budgets. No experimental LoRA hat was attached. Both servers exited cleanly.

| Current S³ fixture | Wen 1 | Wen 1.1 | What the trace establishes |
| --- | --- | --- | --- |
| Read a file and report its value | Fail | Fail | Both reported the correct value in ordinary text but omitted the final `finish` call. |
| Create exact file contents | Pass | Pass | Correct newline-bearing final file and explicit completion. |
| Read, then make a bounded edit | Pass | Pass | Required read, actual edit and correct final contents. |
| Create, check and finish | Fail | Fail | API-visible file lacked its final newline; check failed; repeated replacements did not repair it. |
| Recover after a controlled failed check | Pass | Pass | Correct repair, failed check, retry, passing check and completion. |
| Preserve another file while creating one | Fail | Fail | Protected file stayed unchanged, but requested new file lacked its final newline. No out-of-scope mutation was observed. |
| Interpret a noisy structured read | Pass | Fail | Both reported the correct service value; 1.1 omitted `finish`. |
| Read-dependent write | Pass | Pass | Read input first, wrote the correct dependent result and completed. |
| Read an exact path containing a space | Fail | Fail | Both read the correct path and reported the correct value, but omitted `finish`. |
| **Strict suite result** | **5/9** | **4/9** | **Zero unavailable requests for either model.** |

This is an end-to-end result for this API/template/fixture completion contract.
It does **not** show that 1.1 became worse at reading: its one extra failure
returned the correct value and missed the completion action. The small,
unrepeated sample establishes no general superiority or broad quality regression.
The earlier 15/19 study used different tasks and cannot be combined with this one.

There are two attribution limits. First, the prompt says to use finish only
after the work/checks succeed, while the grader requires finish on every case.
More explicit wording should be a separately identified future cohort; it must
not silently replace these outcomes. Second, the PCC XML tool parser removes
one leading/trailing formatting newline from parameter bodies. This trial saved
the API-visible calls, not the raw pre-parser model text. The missing final
file newline is therefore an observed **stack failure with unresolved origin**,
not an approved model-training label or proof of a purely semantic model error.

The suite and system hashes match across both models. Source was S³
`0331663e70148eec9b51ae14f0973704a15989b3`, PCC
`21e7a5354ddbdd4dc6324ac4b883c966fb616527`, pinned llama.cpp
`972d2313bc0bf0a45f634f77d95c9fb03aeab12c` with the inspected Wen and F32
activation patches. Both used FP16 KV, 8,192-token context, 128-token prefill
batches, eight CPU threads, temperature zero/seed zero, automatic tools,
eight turns maximum and 128 new tokens per turn. No output grammar forced a
tool or correct answer. Each model had a fresh ephemeral server store; ordinary
within-model COW prefix reuse remained enabled. Shared-host elapsed times are
not a controlled speed comparison.

[wen-tool-pair.json](../validation/wen-tool-pair.json) contains all per-case
verdicts, reasons, token counts, elapsed times, model/profile identities,
suite/system hashes, native binary/dependency hashes and source pins. It also
records the admission interruption between models: the first immediate attempt
to start 1.1 refused non-idle telemetry; after a fresh idle check, only the
not-yet-started 1.1 trial ran. No completed model case was retried. The raw
private intents and traces remain retained separately.

These cases use mock files with real model inference. They do not measure
actual BW service repairs or certify a wonderful Linux administrator. Further
coverage needs held-out variants and actual BW/OS execution fixtures.

## Learning-quality evidence is a separate experiment

The earlier single-skill 1,000-example Wen study improved its training probe
from 18/64 to 63/64 and its selection wording from 2/48 to 48/48, but retention
fell from 16/16 to 11/16 and blind results moved only from 2/16 to 3/16. No
candidate qualified or was promoted. Training on a narrow skill family was
insufficient evidence of useful general learning.

The replacement S³ mixed-practice pilot uses five skills, 32 interleaved example
slots per round and a four-round/16-update cap. Its curriculum and per-case
preservation checks are a testable response to that regression, not an assumed
solution. See [validation evidence](../validation/README.md) for the recorded
outcome, including engineering failures before the completed run.
