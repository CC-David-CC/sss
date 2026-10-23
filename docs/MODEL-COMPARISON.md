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

The first paired trial runs **Wen 1, then Wen 1.1**, on the same nine original
tool fixtures, using the same selected A100, native adapter, prompt, case order
and budgets. No experimental LoRA hat is attached. See [the fixed protocol](BENCHMARKING.md).
Results will distinguish model failures from unavailable backend requests and
identify the exact source/model hashes. Until the paired evidence is complete,
neither model has a published score on this suite.

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
