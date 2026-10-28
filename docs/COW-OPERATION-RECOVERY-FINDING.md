# COW operation recovery finding

The two incomplete MiniCPM/BW operations have no recovered durable completion.
Their saved BW journals and COW stores remain private and must be retained. An
idle worker or a missing durable receipt does not establish that either request
failed before committing.

Source inspection explains a limitation of the current recovery interface:

- COW's coordinator keeps admitted request handles and their `queued`, `failed`,
  `cancelled`, or `durable` states in its process. The operation-status API can
  report these while the owning coordinator remains alive.
- After reconstruction, the API can recover a validated durable publication
  from the store. A missing publication does not establish an abort. The
  process-local failed state is not itself a durable failure receipt.
- Publication failures may retain retryable data in the running process. The
  publication retry path is distinct from rerunning model computation.

For future incidents, query the original operation's status **before stopping or
restarting its coordinator**, preserve the returned scope and evidence, and
check whether publication recovery is offered. Capture the client-side error
and service diagnostics privately. A process-local failure is useful diagnostic
evidence but is not a crash-safe proof that no publication committed.

The next implementation investigation should examine whether COW can persist a
terminal failure receipt bound to the original intent, with committed publication
taking precedence and ambiguous crash windows remaining unresolved. BW would
need to consume such a receipt without replaying or inventing an operation ID.
This is a design direction, not a claim that the existing requests are recoverable
or that their precise failure cause is known. Qualify any implementation against
commit/failure races, interruption, restart, and publication retry before using
it to advance a learning run.
