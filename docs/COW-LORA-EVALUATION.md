# Compare an attached LoRA candidate without losing its identity

S³ uses PCC's existing COW request path for this optional evaluation. PCC owns
the immutable base-plus-adapter model and native execution. S³ owns the cases,
grading, learning/forgetting reports and complete-result merges. BW continues
to own agent workflows and tool authority.

`sss_integration.optimizer_evaluate --execution-path cow` accepts a PCC profile
with one explicitly pinned adapter. The ordinary model argument and
`model_sha256` field identify the **base GGUF file**. Every COW intent, case and
result additionally records:

- `candidate_model_contract_id`: PCC's actual composite contract, including the hat.
- `candidate_adapters`: the exact adapter SHA256 and scale, or an empty list.

The full original profile is retained in the intent. Numerical runtime identity
describes the implementation and math policy; changing the candidate's hat does
not pretend to change the runtime implementation. The execution profile and
model contract still change, so COW cannot reuse another hat's model state.

Shard collation requires the same composite binding on every shard. A missing,
malformed or different binding is an infrastructure failure, even when all base
GGUF hashes agree. Old base-only evidence without these additional fields remains
readable, but cannot be mixed with partially identified new shards.

CPU identity, collation and adapter tests pass. The new attached-hat path also
passed a bounded shared-A100 qualification: eight full-vocabulary frontiers
matched the independent fresh oracle exactly, both state restores were exact,
and two shared-root greedy requests matched their references. Full 864-case
F16/F32 baselines and the already-trained first hat are being assessed separately. The existing full-weight controllers
continue on their frozen source snapshots. This new wiring does not waive the
earlier failed merge-equivalence gate or certify a complete LoRA learning curve.

See [PCC's owner workflow and qualification limits](https://github.com/CC-David-CC/Private_Context_COW/blob/feat/native-learning-curves-20261024/docs/DENSE-LORA-COW.md).


## Separate direct-hat learning curve

The original per-update study made merged-F32 parity an entry gate for its LoRA
arm. That gate failed and remains failed. The attached-hat curve is an explicit
execution amendment: independently qualified direct COW inference replaces the
merged deployment only for this separately labelled measurement. It does not
make the original merged-deployment arm pass.

Training resumes the exact saved AdamW rank-16 adapter and optimizer moments from
update 1. It does not repeat initialization or the first update. The ordered
practice stream, batch of 27, learning rate and 68-update endpoint remain the
predeclared recipe. Each new update requires finite gradients, independent
adapter reload within the unchanged loss bound, and a complete 864-case direct
assessment. The first saved hat and F16/F32 baseline controls are assessed
independently; a baseline still in progress cannot count as a measured result.

Reports must label this series **LoRA, attached adapter**, carry its actual
runtime/model identities, and show gains and losses. A standalone merged GGUF
requires its own retained numerical and behavioral evidence. No model promotion,
threshold relaxation or merged-model qualification follows from this amendment.
