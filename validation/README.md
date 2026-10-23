# Measured status

The standalone package and integrations pass their bounded checks. No
language-model ability is qualified by package/unit tests or a controlled evaluator.

| Check | Observed outcome |
| --- | --- |
| Fresh core-only Python environment | 28 tests pass; core installation has no runtime dependencies; CLI smoke and dependency checks pass. |
| Optional PCC controller integration | 12 tests pass against the real lesson store, with explicitly controlled model/evaluator callbacks. |
| Both clients plus real native CPU updates | Four native runs pass across two guarded jobs, including mixed replay, targeted repair, saved-hat continuation and reconciliation. |
| Earlier single/batch/full workflow through extracted fixtures | Passes actual BW checks, HTTP, native updates, final short batch, full continuation and reload. |
| BW lesson/client/terminal regressions | 35 tests pass against the matching preview source. |

[cpu-guard.json](cpu-guard.json) is a public-safe record of the native CPU guard
proof. Its skill regression and recovery are deliberately injected. Those scores
are **not** native language inference or spontaneous model failures. The fixture
is a generated two-layer model, not Wen. No GPU is used and no candidate is
promoted. Reconciliation does not create extra native runs.

The original six host-trace grader scenarios and three added argument/noisy-output/
dependency scenarios are checked with positive and distinguishing negative traces.
They consume host-validated evidence; plain model-authored dictionaries are not
proof of actual tools. No upstream benchmark score or whole-agent success is claimed.

A first bounded Wen mixed-practice trial captured baseline results, then stopped
in PCC's native graph expansion before producing a complete guarded candidate.
This was a native-engine infrastructure failure. A larger graph-node capacity
subsequently passed CPU self/chain checks and an independent FP64 reference:
386 scalar gradients, with maximum measured errors 1.7283e-8 and 1.035996e-7
under the original tolerances. No tensor operations or CUDA kernels changed.

The completed two-A100 native pilot then consumed **four rounds, 16 updates and
128 interleaved example slots**. Every round included all five skills. Baseline
and final validation were identical: add 4/8, multiply 7/8, absolute value 3/8,
floor 0/8 and ceiling 0/8, or **14/40 overall**, with no lost protected successes.
No candidate qualified; blind evaluation was correctly withheld because
validation never qualified. Nothing was promoted and the base model remained
unchanged. [wen-mixed-pilot.json](wen-mixed-pilot.json) records source/binary/model
identities, all four candidate hashes and per-round distributions/scores.

This establishes bounded real training/whole-tree evaluation mechanics and
preservation for these particular checks. It demonstrates **no held-out gain**
and does not establish general coding, administration or broad retention.
128 consumed slots need not mean 128 distinct examples. The budget was small;
the result does not establish that mixed practice cannot work at another tested
budget, nor justify advertising an improving hat.

The extracted native-oracle adapter initially omitted its POSIX lock-module
import. A second study stopped before model inference/training on that path.
Three distinguishing adapter tests reproduced the missing import, then passed
after the fix: real lease exclusion, inherited worker lease, unchanged idle
thresholds and refusal to launch without admitted headroom. GPU inventory and
child creation are mocked in those tests; they are not GPU/model results.

A later attempt refused a busy evaluation GPU before inference rather than
relaxing admission. The completed run evaluated on a training GPU sequentially
after training resources were released. Prior failures are retained separately;
they are not silently replaced by the successful mechanics run.

The model-only tool runner has separate distinguishing checks for all nine
scripted fixture solutions, inaccessible real files/shell, parallel-call
rejection, malformed model arguments, unavailable backend outcomes without retry,
and request-intent persistence before authenticated POST without key logging.
These tests prove the harness behavior, not a model's score. Actual paired Wen
results belong in [the model report](../docs/MODEL-COMPARISON.md).

The first paired real Wen tool trial is complete: **Wen 1 5/9; Wen 1.1 4/9**,
with zero unavailable requests. [wen-tool-pair.json](wen-tool-pair.json) retains
the complete public-safe summary and matching manifests. Both servers exited
zero. The extra 1.1 failure was correct read content without the required finish
action. Two shared file-content failures have unresolved model/parser attribution
because pre-parser XML text was not saved. Read the detailed report before
interpreting these strict end-to-end scores as model ability.
