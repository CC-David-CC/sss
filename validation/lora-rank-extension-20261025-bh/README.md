# First matched-update LoRA rank observations

The [rank study](../../docs/LORA-RANK-EXTENSION.md) uses the same original model,
ordered practice and frozen 864-question development panel. At one update and 27
presentations, the six ranks have a completed direct-adapter COW assessment.
The [summary](summary.json) retains paired answer/completion gains and losses,
model/adapter/runtime identities, alpha/rank and native/reload receipts.

Rank 1 now works after the credited edenfunf/llama.cpp30142 CUDA fix. Its saved
first update was assessed without retraining. A second native update resumed
that exact adapter and optimizer state, reached cursor 54, produced 590 finite
gradient tensors and reloaded at error 1.9868e-7 under the unchanged 2e-4 bound.
That validates the recorded continuation; it is not a bitwise comparison with
an uninterrupted two-update rank 1 run. Assessment 2 was pending at export.

The exporter itself ran no model call, training job or model/state write.
The underlying training/assessments are the actual observations reported here.
No merged standalone model, tuned rank optimum or release is established.
