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
