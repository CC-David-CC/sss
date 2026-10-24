# Repeating the real-client CPU protocol checks

The actual Codex, OpenCode and pi CLIs can each complete a deterministic
read/write/edit/verify workflow inside a disposable Linux namespace. Each runs
four real tool calls and five mock model requests. The fixture checks that the
original tool results reach subsequent requests and independently checks the
resulting files. **No model inference, weight update or Wen quality measurement
occurs.** This is an opt-in integration test, separate from S³'s stdlib core.

The [validation record](../validation/learning-program-20261024/real-cli-transport.json)
contains source and package-lock hashes, actual tool names, settled boundary
receipts, environment versions and limitations. The clients were:

| Client | Installed package | Version | Tools exercised |
| --- | --- | --- | --- |
| Codex | `@openai/codex` | 0.164.0 | Four `exec_command` calls performing file operations and verification |
| OpenCode | `@opencode/cli` | 2.1.4 | `read`, `write`, `edit`, `shell` |
| pi | `@earendil-works/pi-coding-agent` | 1.4.0 | `read`, `write`, `edit`, `bash` |

These are exact version pins, not aliases for every release of the projects.
OpenCode 2.1.4 is distinct from older `opencode-ai` distributions. Its current
native file tools use `path`, and its command tool is `shell`. pi 1.4.0's edit
tool requires an `edits` list. The first probe caught these argument differences
as failures. In particular, a successful client process exit did not turn a
protocol failure into a passing workflow. The corrected probe passed all three.

## Preparation

Use an explicitly authorized Linux development host. The measured environment
had Python 3.14.4, `/usr/bin/node` 22.22.1 and bubblewrap 0.11.1, with unprivileged
user namespaces enabled. PCC's selected Python protocol modules also need their
normal Python dependencies, including Jinja2. The launcher uses S³'s existing
`LinuxSandbox`; it does not install software or submit GPU work.

Install each exact package in a separate owned prefix, retain its
`package-lock.json`, inspect the package's setup requirements, and verify its
actual `--version` and `--help` inside a disposable environment. Codex and
OpenCode require their matching native platform binaries. OpenCode's package
postinstall prepares its native executable; installing with scripts disabled
requires inspecting and completing that preparation separately. The S³
launcher refuses a different package name/version or a missing dependency lock.

Create a private JSON file mapping client names to the three installed prefixes:

```json
{
  "codex": "/your/owned/codex-prefix",
  "opencode": "/your/owned/opencode-prefix",
  "pi": "/your/owned/pi-prefix"
}
```

Use an inspected PCC checkout. Only `serve/__init__.py`, `serve/frontend.py` and
`serve/responses.py` are copied into the protocol snapshot. Its revision and
the actual copied bytes are recorded separately. No model, PCC store, provider
credentials, host home or protected evaluation pack is mounted.

## Run once and inspect the original directory

From the S³ source checkout:

```sh
python3 -m sss_integration.external_apps_cpu \
  --output /your/private/new-client-proof \
  --prefixes /your/private/prefixes.json \
  --pcc-root /your/inspected/PCC
```

The output directory must be new. The launcher runs each original client once
inside its own filesystem, process and network namespaces. Its only endpoint
is a loopback fixture inside that namespace. The installed client and selected
PCC protocol files are read-only mounts. The home directory and files are
disposable. The fixture process rejects accidental direct invocation; the
launcher supplies the outer isolation before any client starts.

The launcher prints one aggregate result per client and writes `results.json`,
`manifest.json` and private boundary receipts. Each client directory contains
its exact configuration, original event output, requests, tool calls and final
files. Keep those private. Examine both `passed` and the boundary's settlement,
timeout and exit status. Inspect failed original evidence before changing a
fixture or declaring a new run; an observation timeout is not permission to
start a duplicate operation. Bubblewrap's namespace init and the existing
LinuxSandbox timeout handling bound and settle the test's child processes.

Codex's internal configuration allows tools within the prepared world; the
outer bubblewrap boundary supplies containment. Do not copy that configuration
into an ordinary host session. OpenCode uses `--standalone`, and pi disables
external extensions, MCP and context-file discovery. No API account is needed;
the configured key is an explicit fixture string.

## What is established and what comes next

Codex uses PCC's actual Responses input parser, tool-name mapping and output
assembler for a five-request tool loop. PCC already supplies this protocol;
the check does not introduce a new inference engine or a replacement for BW's
native COW context protocol. OpenCode and pi consume synthetic Chat Completions
streams. All three execute their real installed tool implementations.

This does not exercise PCC's native model backend, Wen's tokenization or tool
selection, inference errors, compaction, cross-session persistence, or the
independent task-receipt exporters required by the
[four-condition comparison](HARNESS-COMPARISON.md). It does not qualify matched
sampling across clients. Mock usage and short fixture timings cannot support
model cost or harness performance claims. Package/source hashes bind the
trusted operator's setup; they do not attest an arbitrary installed tree.

Next, connect the same fixed PCC-served Wen to each client and preserve the
actual backend identity and effective request settings. Verify tool results,
continuation, usage and explicit error paths before running the baseline,
general probe, task probe and composed comparison. Keep original host operation
IDs and permissions; S³ remains the curriculum and evidence auditor.
