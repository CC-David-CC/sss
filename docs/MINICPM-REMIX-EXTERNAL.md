# Published Q5 versus original FP16: independent spot check

Inference only on llm-60, with identical llama.cpp build, greedy decoding,
thinking disabled, 512 output tokens, and eight concurrent requests. No weights
changed. This uses the first 32 test rows from each public dataset, not the
S³ foundation panel or training lessons.

| Test | Original FP16 | Original Q5 | Trained update-68 Q5 |
|---|---:|---:|---:|
| GSM8K | 22/32 | 24/32 | 20/32 |
| ARC-Challenge | 24/32 | 23/32 | 25/32 |
| Total correct | 46/64 | 47/64 | 45/64 |
| Naturally finished | 59/64 | 60/64 | 61/64 |

Against original FP16, six answers became correct and seven became incorrect. Against original Q5, the trained Q5 gained six answers and lost eight. Quantization alone caused no net score drop on this sample. This small sample does
not show an overall improvement. It compares usable models at different storage
precision and training state; it does not isolate training or quantization.
Public questions may have appeared in base pretraining. This is not an official
GSM8K/ARC leaderboard protocol: GSM8K requires the requested `####` numerical
answer; ARC requires exactly the option label. Formatting failures count as wrong.

[Verified counts and response hashes](results/minicpm-remix-external-20261027/verified-summary.json)
bind all 128 saved responses. The saved response JSON files and frozen dataset payloads are included beside
the receipt, so the scores can be checked without generating new answers. The runner is included with
the evidence; its frozen downloaded dataset payload hashes are in the receipt.
The owner subsequently approved adding this table and its limitations to the Hugging Face card.

Datasets: https://huggingface.co/datasets/openai/gsm8k and
https://huggingface.co/datasets/allenai/ai2_arc (ARC-Challenge configuration).
