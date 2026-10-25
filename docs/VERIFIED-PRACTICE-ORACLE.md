# Verified synthetic practice oracle

S³ owns the fixed checker, immutable owner-installed cases and grading. BW owns
execution and its namespace retirement. This optional pathway does not register
a lesson, select targets, call a model, train, or grant an agent authority. Its
result always says `lesson_approved: false`. The protected five-case foundation
checker and dispatch are unchanged.

The first family is `affine-clamp-fold-v1`: a single `task.py` defines
`solve(values, scale, offset, low, high)`, returning exactly
`{'values': transformed, 'total': sum(transformed)}`, where each transformed item
is `min(high, max(low, scale*x + offset))`. Inputs are newly authored synthetic
practice rows. They are independent of existing diagnostics and held-out answers.

```python
from hashlib import sha256
from sss.practice_oracle import AffineClampFoldCase
from sss.adapters.bw_practice_oracle import observe

case = AffineClampFoldCase.install('my.affine.001', 'practice-v1', [
    dict(values=[-5, 0, 3], scale=2, offset=1, low=-4, high=6),
])
source = captured_task_bytes  # Owner supplies exact artifact bytes, not a path/tool command.
result = observe(case, source, sha256(source).hexdigest(), fresh_private_output)
```

Installation requires explicit case and split identifiers and canonical immutable
JSON bytes. The constructor and observation API validate the case; even a forged
or mutated frozen instance cannot bypass observation admission. There are 1–32
rows, at most 64 values per row, 16 KiB of canonical inputs, and integer bounds
±1,000,000. Booleans are not integers. Each row has exactly the five declared
fields and `low <= high`. Case/schema/family/split/input hashes bind the owner
descriptor. Changing the checker requires a new reviewed implementation identity.

Sources are at most 32 KiB, strict UTF-8, and must match the owner's SHA-256. The
existing `pure_function` gate is a prerequisite; the new adapter additionally
requires exactly the five named arguments, with no defaults, annotations,
variadic/keyword-only arguments, nested functions, match statements or annotated
local assignments. All loaded names must be arguments, explicit local bindings,
`solve`, or the legacy admitted safe builtins. No builtin name or `solve` may be
rebound (including comprehensions and exception-handler bindings). Rejecting all
builtin bindings also prevents a comprehension-local `eval` binding from being
mistaken for permission to load global `eval` elsewhere. This
closes aliases such as `solve=eval`, `min=eval` and `sorted(..., key=eval)` without
altering the legacy checker. Imports, I/O, classes and arbitrary calls are refused.
These gates run only in the optional adapter; the core is stdlib-only and imports
without BW/PCC installed. An invalid
source contract is a clear FAIL with `execution_attempted: false`; a wrong source
pin or unsupported/invalid case is refused before creating an evidence directory.

The adapter uses BW `Executor`, `NamedCommand` and `execute_command`, with a fixed
Python driver and a five-second limit. Only the captured `task.py` is projected
read-only, with no writable outputs grant. Explicit input rows enter the driver;
host expected results and checker modules never enter its namespace. The actual
BW input receipt must contain exactly `task.py` with the pinned hash and byte
count; matching source files before/after alone is insufficient. A missing,
extra or different captured input makes the result UNAVAILABLE. BW verifies
actual distinct namespaces and their retirement before publishing command output.
The adapter does not replace this with LinuxSandbox's weaker settled flag.

The parent computes expected results independently and requires strict JSON,
rejecting duplicate keys and nonfinite constants. Equality is recursive and type
aware: `true` and `1`, or `1.0` and `1`, differ. Returned results and all input rows
after execution must match. A zero exit alone cannot pass. Timeouts, truncation,
unretired or uncertain execution, missing BW runtime and source identity changes
are UNAVAILABLE, never a failed skill or pass. Ordinary settled nonzero exits and
incorrect function behavior are FAIL.

Fresh private evidence retains raw stdout/stderr, their hashes, return code,
disposition, actual BW isolation details, source before/after hashes, command and
BW implementation hashes, fixed checker/gate/adapter/driver hashes and case pins.
`grade_observation` is a host-side helper for this trusted adapter, not a verifier
of arbitrary student-supplied receipt dictionaries. Fault-injection unit tests
exercise grading decisions and are explicitly separate from actual BW runs.

The CPU integration tests execute a correct reference, incorrect affine logic,
constant output, input mutation and Boolean substitution. A separate BW boundary
test proves self-edit attempts fail on the read-only projection; such code also
fails the pure source gate without execution. Unit cases cover forged output,
duplicate/nonfinite JSON, unsupported/forged cases, wrong pins, oversized sources,
timeouts, truncation and unretired evidence. None qualifies model learning.

Run core/legacy tests without BW; run the explicit optional integration module
only on an authorized Linux host with BW and its existing namespace prerequisites:

```text
python -B -m unittest discover -s sss_tests -p 'test_*.py'
PYTHONPATH=/path/to/sss:/path/to/branchwrite python -B -m unittest sss_integration.test_bw_practice_oracle -v
```

A later provider may supply an immutable BW capture artifact's exact source bytes
and pinned hash. This API does not claim that capture registration, artifact
authentication, exact target derivation or approval is integrated. No provider
stub or alternate workflow runtime is introduced.
