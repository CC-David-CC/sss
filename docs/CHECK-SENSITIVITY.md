# Does a proposed check detect the bug?

A check can pass while the saved program is wrong. In the earlier MiniCPM BW
probe, a proposed shell check claimed to cover difficult filenames but used
simple paths. The new S³ check-sensitivity pathway replays that exact proposed
check against a correct reference and two independently graded faulty programs.
It uses BW's real interpreter, grants, command receipts and restricted Linux
namespace, then a separate S³ behavior check of the saved files.

| Check | Correct reference passes | Unquoted source expansion caught | Empty output caught |
| --- | --- | --- | --- |
| Existing model-proposed command | Yes | No | Yes |
| Operator-authored difficult-path and byte-assertion control | Yes | Yes | Yes |

These are six host-controlled executions on three declared program variants,
not six language-model trials. They establish the weakness of this particular
check and the sensitivity of this particular control. They do not establish a
general mutation score, a MiniCPM improvement or a fixed BW workflow. No model
inference, GPU allocation, training or promotion occurred.

## Use the pathway

On an authorized Linux host with the actual BW checkout and bubblewrap available:

```bash
python -m sss_integration.check_sensitivity \
  --bw-root /owned/BranchWrite \
  --output /owned/new-private-check-probe
```

The default proposed check is an explicitly weak, operator-authored syntax check.
To examine an owned proposed command instead, add `--check-file /owned/check.json`,
whose JSON has exactly `name` and `command`. This does not ask a model to generate
another command. The command is executed with actual BW grants and bounded
resources; inspect it and use an owned task before running it. Raw commands,
programs, task histories and tool output stay in the private output directory.

Independent observations run concurrently, each in its own BW world and ledger.
The adapter records the unchanged source bytes, actual command disposition,
exit code, retired namespace, independent oracle evidence and BW implementation
identity. S³'s pure `sss.studies.check_sensitivity.assess` reducer uses these
observations; it does not execute commands or own a second workflow runtime.
The core stays importable without BW, PCC, NumPy or a GPU.

## Qualification requires a positive control

A check must pass the independently correct reference **and** reject every
declared faulty variant. A broken command that fails on everything is not a
good test. The reducer distinguishes:

- `DETECTS_DECLARED_MUTANTS`: reference passes and all declared faults are caught.
- `MISSES_DECLARED_MUTANTS`: reference passes but at least one fault is missed.
- `REFERENCE_CHECK_FAILED`: even the correct reference fails the proposed check.
- `INVALID_VARIANT_SET`: the oracle did not establish a correct reference and
  genuinely faulty variants.
- `UNAVAILABLE`: command settlement, source stability or bounded execution is
  missing. Timeouts are not counted as caught bugs.

Different commands, checkers, BW implementations or duplicate program identities
cannot silently be combined. Independent oracle timeouts and incomplete output
also prevent an available observation. Partial execution remains a partial
probe, with errors retained rather than replaced with invented verdicts.

This distinction caught an engineering defect in the first control run: BW's
namespace did not provide `/bin/sh`, even though `/usr/bin/sh` was available.
The control failed on the correct program, so S³ refused to qualify it. A PATH
version passed before the BW fix; the canonical `/bin/sh` version passed after
the explicit read-only namespace alias was added. All three observations are
preserved separately. The negative control was not erased or relabelled.

## Feed the finding into learning without teaching the test

Record the failure class: a check description is not evidence that it exercises
the named behavior. Generate fresh practice programs, difficult paths, contents
and independently checked demonstrations. Include both valid and faulty cases;
require assertions of status and output bytes. Retain previously successful
families in mixed review. Keep diagnostic programs, hidden checks and original
evaluation answers out of practice. The existing 68-update comparison's practice
order and controls remain frozen.

Check sensitivity is evidence for lesson review, not lesson approval or model
promotion. The learning program still needs a verified lesson, native PCC
admission, independent learning/retention tests and a declared acceptance policy.

[Public aggregate evidence](../validation/minicpm-native-learning-20261024/check-sensitivity-aw.json)
contains hashes and outcomes, not the original private model response.
See also [the earlier BW experiments](https://github.com/CC-David-CC/BranchWrite/blob/feat/native-learning-path-20261024/docs/MINICPM-CHECK-PROGRESS-EXPERIMENT.md)
and the [operator handoff](OPERATOR-HANDOFF.md).
