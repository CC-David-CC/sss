# Start here: explore one skill safely

S³ is the school and test laboratory. It describes skills, makes exercises,
checks results and records whether earlier abilities survived. BW is the working
agent. PCC runs the model, manages its saved context and owns native training.
A smaller model can drive the bounded experiments below by following the checks.
It does not need to redesign the math graders, infer GPU availability or decide
that a candidate is safe to install.

This development builds machinery. Reference demonstrations and tiny generated
CPU weight updates do not show that Wen learned these skills. Current live Wen
qualification is pending. Many graph branches remain planned.

## Start without a model or GPU

Use Python 3.11 or later in a checkout of this repository, on an authorized host.
The core needs only Python's standard library. Each output directory must be new.
Keep run directories outside public source; they can contain evaluation material.

```sh
python -m sss explore doctor
python -m sss graph
python -m sss exercise --skill math.add.carry --split practice --reference
python -m sss explore reference --directory /your/private/new-reference-run --skill math.add.carry --skill math.fraction.add
python -m sss explore inspect --directory /your/private/new-reference-run
python -m sss report --output /your/private/reference-report.html --assessments /your/private/new-reference-run/assessment.json
```

Expected: doctor says `ready`; the reference run records all nine cases per skill
as passing. Its qualification is **false** because nine examples are only a probe.
Open the HTML in a browser. It needs no internet connection.

`python -m branchwrite skills` imports the same graph when S³ is installed in
BW's environment. `python -m branchwrite skills explore doctor` delegates to S³.
The former active-tree interface remains at `branchwrite skills legacy` and
`branchwrite skills --active FILE`.

## Try an explicitly authorized model endpoint

First follow [the operator handoff](OPERATOR-HANDOFF.md). The endpoint must already
be authorized and running. These commands never start a server or reserve a GPU.
Use the model's actual ID, inspected revision, tokenizer and template identities,
application revision, thinking mode and context settings in a profile JSON.
[`examples/profiles/owned-endpoint.json`](../examples/profiles/owned-endpoint.json)
is a template; its placeholders deliberately fail admission.

```sh
python -m sss explore prepare --profile /your/private/model-profile.json --directory /your/private/new-probe --skill math.add.carry
python -m sss explore run --directory /your/private/new-probe --endpoint http://AUTHORIZED_ENDPOINT/v1 --maximum-output 512 --maximum-seconds 600
python -m sss explore inspect --directory /your/private/new-probe
python -m sss report --output /your/private/probe-report.html --assessments /your/private/new-probe/assessment.json
```

Set the API key privately in `SSS_API_KEY` if needed. Do not put it in Git, a
profile, a prompt or a screenshot. The endpoint's thinking renderer must match
the declared profile. Different modes receive separate results. Provider token
usage is reported usage; it is not an independently measured rendered-token count.
Long-context admission requires the exact tokenizer/template and its separate
PCC validation, beyond this direct-answer command.

A probe has three examples at each of three gates. A qualification uses the
explicit `prepare --qualification` flag and freezes 256 per gate. Do not run a
qualification until the operator has chosen the distribution and frozen its
critical and retention packs. The Python `freeze()` API accepts those packs;
the simple CLI does not yet compose a whole-model preservation campaign.

## Find the rest

- [On-disk organization](ON-DISK-LAYOUT.md): subjects, prerequisites and difficulty coordinates.
- [Operator handoff](OPERATOR-HANDOFF.md): exact workflow, stop conditions and evidence.
- [Implementation plan and remaining gates](FOUNDATIONS-PLAN.md).
- [Completed synthetic teaching examples](../examples/finished-training-examples/).
- [Existing model findings](MODEL-COMPARISON.md): separate historical model measurements.

## Existing BW domains

See [Blender, build123d and other BW workflow recipes](BW-WORKFLOWS.md) and
`python -m sss workflows list`. Existing execution and version-scoped evidence
are mapped to S3 prerequisites. The operator prepares domain environments;
new per-cell model qualifications remain separate.

CPU checkpoint: [dated validation](../validation/foundations-20261023/README.md).

## Preparing a guarded training pilot

See [Foundation training pilot](FOUNDATION-TRAINING-PILOT.md) for the progressive-graph adapter, exact PCC rendering, private practice TXT export, measured Wen baselines and current training-capacity limit. This operator API does not replace the existing CLI adapter.
