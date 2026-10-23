# Comparing models on the same tool tasks

`sss bench tool-use` sends real model requests to an explicitly selected
OpenAI-compatible server and interprets returned calls against **in-memory
fixture files**. It cannot execute shell commands or access the host filesystem
through those tools. It is a model benchmark, not a second BW runtime.

## The fixed first suite

The nine original cases cover read, write, edit, checked completion, recovery,
scope, noisy reads, a read-dependent write and an exact path containing a space.
`sss suite tool-use` lists them. The grader checks completed fixture events and
actual resulting contents. All cases require an explicit final `finish` call.
Recovery deliberately injects one transient failed check so both models face
the same recovery requirement. This is a controlled fixture, not an organic
operating-system failure. Evaluation cases are not a practice-data export.

Each assistant turn may make one tool call and inspect its result before the
next turn. The first comparison uses temperature zero, seed zero, at most eight
turns and 128 generated tokens per turn. Tool choice is automatic, with parallel
calls disabled. There is no output grammar forcing the correct tool or answer.
The serving template still supplies the model's ordinary tool-call format.

Use identical suite bytes, system prompt, case order, hardware, native build,
context/batch settings and budgets for a paired model comparison. Start each
model with a fresh server store and use separate immutable output directories.
Record any backend prompt reuse within a model run. Shared-host contention can
affect elapsed time, so these short trials primarily measure correctness.

## Run it

Configure a supported model server first. The endpoint below is an example API
root, not a discovered server. Keep the key in the process environment; do not
put it in the metadata file or command line. Write public-safe model and engine
identities into a metadata JSON file, for example:

```json
{"model":"YOUR_MODEL","model_sha256":"ACTUAL_SHA256","hardware":"ACTUAL_GPU","native_build_sha256":"ACTUAL_SHA256","context":8192,"prefill":128,"threads":8,"math_profile":"ACTUAL_PROFILE"}
```

```sh
sss bench tool-use --endpoint http://127.0.0.1:18080/v1 --model cow \
  --metadata /private/model-metadata.json --output /private/new-trial \
  --max-turns 8 --max-new-tokens 128 --seed 0
```

The output directory must be absent. It contains a suite/system manifest,
private request intents written before each POST, private fixture traces and a
summary. Authorization headers are never written. Raw model outputs may still
contain private material; output is not automatically safe to publish. Exit
code three means at least one case was not a pass; inspect the statuses.

There is **one POST per intent and no automatic network retry**. A lost response
or backend error produces `unavailable`, because the outcome is unknown.
Malformed model tool arguments, parallel calls, out-of-scope mutation attempts
and stopping without verified completion produce failures. These distinctions
must survive report aggregation. A later retry is a separately identified run.

## Interpret the result

A nine-case pass rate is a small diagnostic sample. It is not a Linux admin
certification, broad coding benchmark, sustained-load test or statistical claim
of superiority. Repeat and expand with independently authored held-out variants
before drawing stronger conclusions. Do not teach from these evaluation cases.

The host-trace grader can also consume evidence from a real BW adapter. That
adapter must first validate BW's actual receipts and final objects. A model or
caller constructing plausible event dictionaries does not prove execution.

Historical Flash Q4/Q8 throughput and native checkpoint-oracle tests use other
protocols. Keep them in separate tables. They cannot fill missing cells in a
same-suite Wen comparison or establish agent task quality.
