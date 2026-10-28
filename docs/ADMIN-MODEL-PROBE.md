# MiniCPM admin and code diagnostic

The original MiniCPM5-2B FP32 and Remix 2 (rank-32 AdamW update 42, merged FP32)
completed the same small panel on the same llm-60 llama.cpp server build.

| Domain | Original | Remix 2 |
|---|---:|---:|
| Simulated tool and admin interaction | 4/4 | 4/4 |
| Python and shell fixes, executed in isolated Linux | 5/5 | 5/5 |
| Configuration repair, parsed in isolated Linux | 1/2 | 0/2 |
| Total | 10/11 | 9/11 |

The configuration failures appended `protected.txt` as an extra line in the INI
file. Both models did this in the port task; Remix 2 also did it in the logging
task. The original logging repair passed. Hidden host-side checks parse the
actual saved INI file, compare settings, and verify protected-file preservation.

This is a custom diagnostic JSON action protocol, not a BW, native function-call,
or general Linux administration benchmark. Tool tasks run in memory, coding
checks execute in bubblewrap, and configuration checks use real disposable files
inside bubblewrap. No system services, packages, networking or host processes are
administered. Four tool tasks permit up to eight turns. Code and configuration
tasks receive a single response. Sampling is greedy, thinking disabled, with
1024 output tokens and an 8192-token server context. No training was performed.

Reference controls: the earlier five-code-task real Linux qualification passed;
two configuration fixtures passed six checks (broken, reference, and altered
protected file for each task). Nine tool-fixture contract tests passed locally
and on Linux, including malformed actions and adversarial observations.

An initial grader required unrequested completion wording (`done` and `E42`)
and incorrectly failed two tool tasks for each model. The checker was corrected
to accept nonempty repair completion and an unambiguous E42 diagnosis. Only the
saved trusted observations were rescored; original verdicts were preserved and
no model attempts were repeated. This correction is part of the report, not
evidence that either model improved.

Source: `sss/suites/admin_tool_fixtures.py`, `sss/suites/linux_admin_config.py`,
and `sss_integration/admin_model_probe.py`. Reference sequences, grading rules,
and expected answers are not included in model prompts. A model must not supply
its own final-state or execution evidence. The diagnostic adapter is separate
from BW's workflow authority. Model and server identities and per-case results
are retained in the accompanying aggregate evidence.

These 11 tasks are developmental and too few to estimate a general capability
rate. Broader unseen variants, actual shell observation/repair loops, and native
tool-calling through the existing BW harness remain future coverage. This panel
is not a basis for claiming mastery of the planned S³ admin catalog nodes.
