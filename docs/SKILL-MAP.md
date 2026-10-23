# From primitives to a useful admin assistant

Read/write/edit/finish are foundational behaviors. They need tests of both the
actual effect and the model's next decision: read the intended file, preserve
unrelated text during an edit, interpret a failed check, and finish only when the
requested result is verified.

BW already exposes tools for file reading/creation/replacement, mode changes,
tests, local commands and named remote commands/checks/uploads. Browser, PDF,
CAD and Blender tools are optional. Grants and host configuration decide which
tools exist in a task. This is execution support, not a learned skill rating.

The broad S³ catalog organizes that work into four branches:

| Branch | Primitives and examples | Current measurement scope |
| --- | --- | --- |
| Tool use | selection, arguments, outputs, read/write/edit/finish, dependencies, recovery, scope, receipts | Original file-tool trace graders; model proficiency unmeasured. |
| Linux admin | services/logs/processes, storage/permissions, networking/SSH, config validation, packages, owned GPU jobs | Defined capability map; model test packs not yet implemented here. |
| Coding | inspect source, patch, script, test, review | BW execution support exists; S³ model proficiency unmeasured. |
| Supporting reasoning | arithmetic, units, structured data, paths, quoting, instructions | Five arithmetic-expression leaves have a native evaluator; broader reasoning unmeasured. |

Linux-service repair depends on reading evidence, interpreting commands, scoped
edits, tests and recovery. Coding repair depends on the same foundation plus
understanding source. Arithmetic supports units/capacity estimates; it is one
branch, not the overall definition of a capable assistant.

Administration tests should use owned disposable fixtures and check the actual
result: service state, reachable port, preserved config, permissions and rollback
where applicable. A convincing command string or a mock score alone does not
prove those effects. Testpacks must distinguish unavailable infrastructure from
model mistakes and retain their exact environment and outcome identities.

When activating a branch for training, provide practice examples, validation
cases, blind cases and an independent checker. Unknown/missing coverage cannot
be represented as passing. Parent groups aggregate their children conceptually;
the guard requires every active leaf to meet its declared requirement and retain
previously passing checks.
