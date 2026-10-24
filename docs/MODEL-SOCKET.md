# Connecting an isolated client to one model endpoint

The optional integration adapter connects an actual installed client to a fixed
loopback model port through a filesystem Unix socket. The client keeps its own
tool loop; the declared backend owner keeps inference and resource ownership. The adapter introduces
no workflow ledger, model fallback or automatic retry.

The path is: client HTTP in its isolated network namespace → local relay →
read-only mounted Unix socket → host broker → fixed loopback model port. The
host broker holds the backend key; the workspace receives no host credentials
and has no general network route. Existing LinuxSandbox owns its process and
filesystem boundary. Its original receipt and client events remain private.

## Tested CPU mechanics

All three pinned clients completed four actual read/write/edit/verify tool
operations and five scripted model requests through this transport. Codex used
PCC's actual Responses formatter; OpenCode and pi used scripted Chat Completions
replies. Delegation was disabled in the prepared profiles; no delegation tools
were advertised in the captured Codex request. The host fixture key was absent
from all inspected regular workspace files. No model inference occurred.

The [aggregate CPU evidence](../validation/learning-program-20261024/model-socket-cpu.json)
binds source hashes, client pins, original operations and settled boundaries.
The tests also check streaming before an upstream response finishes, model and
sampling drift, output/call bounds, intent before forwarding, and interrupted
or explicitly failed streams. These are transport tests, not a Wen quality or
cross-harness optimization result.

On an authorized Linux host with the [pinned clients prepared](REAL-HARNESS-SETUP.md):

```sh
python3 -m sss_integration.socket_transport_cpu \
  --output /your/private/new-short-proof \
  --prefixes /your/private/prefixes.json \
  --pcc-root /your/inspected/PCC
```

Choose a short owned output path: filesystem Unix socket names have a platform
length limit, and the adapter refuses an overly long endpoint path. Existing
output directories are refused rather than overwritten or silently resumed.

## Bounds and evidence

`harness_socket.run_client` runs one explicitly prepared task against an
existing model endpoint. The parent supplies the original operation ID, pinned
model alias, context, backend evidence classification, fixture bytes and key
file outside the worker world. The host must verify the actual backend identity
and lease; a supplied JSON identity alone does not attest them.

The current adapter bounds Wen and MiniCPM profiles to at most 131,072 context tokens, 512 output
tokens per call and a bounded number of requests. The broker fills omitted
temperature/seed with zero and an omitted output bound with 512; differing
sampling or excessive output is refused. These normalizations are declared and
the original and sent bytes are separately hashed and durably recorded before
forwarding. Other request fields retain their original semantics.

Each upstream operation has an immutable intent and final receipt. The model
key replaces incoming client authentication at the host and is never logged in
those receipts. Streaming bytes are forwarded immediately and captured privately.
Successful transport requires an API terminal event and, when provided, the
declared response length. HTTP 200 or a closed socket alone cannot establish
completion. An explicit server error is infrastructure evidence; an interrupted
response is uncertain. Either stops further upstream forwarding from this
endpoint, including a client's attempted automatic retries. Reconcile original
native operations before a new experiment; do not infer a model failure.

The client has a 95-second bound inside a 110-second outer fixture bound. Codex
uses a 90-second stream idle allowance in this setup so a short mock-server
timeout does not prematurely reject native prefill. These are explicit initial
qualification bounds, not a long-horizon research budget. Client exit status and
transport completion remain separate from independent task success.

## Live MiniCPM discovery

Six pinned external clients completed actual MiniCPM model/tool exchanges through
this transport and SSH loopback forwarding. Codex, OpenCode, pi and Hermes passed
independent saved-source, output and input-preservation checks. Qwen Code and
DeepSeek failed task checks despite successful transport. See the
[field notes and exact limits](MINICPM-HARNESS-FIELD-NOTES.md). This used native
llama.cpp inference; BW's PCC COW path remains a separate qualification.

The optional adapter accepts the five pinned NPM clients in `harness_pins.py` and
the pinned Hermes source plus its officially built dependency environment. Hermes
source is mounted read-only with an isolated home and runtime. No credentials or
owner config are mounted. The task and optional bounded execution guidance have
separate manifest identities. Discovery GETs outside the endpoint grant remain
recorded denials; they do not invalidate a completed model/tool exchange. Rejected
POSTs, failed or interrupted streams, and unsettled boundaries still prevent
transport completion. Independent task checks remain required.

The pinned pi client reserves 4,096 tokens internally. Declarations at or below
that size are now refused before launch; its live 8K configuration passed.
Hermes's custom-provider path requires at least 64,000 context tokens; provision
real server capacity, as in the measured 65,536-token slots. Its optional title
generation is disabled in this initial profile and auxiliary traffic is configured
for streaming. The full four-condition optimizer and joint weight/harness
comparison remain separate qualification.

The earlier context-size finding used its exact captured profiles. Disabling
delegation changes Codex's tool inventory and may change prompt size; preflight
the effective profile again rather than treating 16K as a universal minimum.
