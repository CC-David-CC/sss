# Measured status

The standalone package and integrations pass their bounded checks. No
language-model ability is qualified by package/unit tests or a controlled evaluator.

| Check | Observed outcome |
| --- | --- |
| Fresh core-only Python environment | 22 tests pass; core installation has no runtime dependencies; CLI smoke and dependency checks pass. |
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

A bounded Wen mixed-practice trial captured baseline results, then stopped in
PCC's native graph expansion before producing a complete guarded candidate.
That is a native-engine infrastructure failure, not evidence that mixed practice
does or does not preserve skills. The original run and its first completed
step are retained. A graph-capacity fix is being checked separately.

The extracted native-oracle adapter initially omitted its POSIX lock-module
import. A second study stopped before model inference/training on that path.
Three distinguishing adapter tests reproduced the missing import, then passed
after the fix: real lease exclusion, inherited worker lease, unchanged idle
thresholds and refusal to launch without admitted headroom. GPU inventory and
child creation are mocked in those tests; they are not GPU/model results.
