# Existing BW workflows in the S³ curriculum

BW has executable workflows for websites, writing, PDFs, build123d CAD,
Blender and explicitly granted remote administration. S³ maps their prerequisites
and provides recipes using BW's actual tools, interpreter, receipts and checks.

```sh
python -m sss workflows list
python -m sss workflows show cad-plate
python -m sss workflows show blender
python -m sss workflows check --bw-root /your/inspected/BranchWrite
python -m branchwrite skills workflows list
```

`check` reads BW's actual tool table, checks referenced files and reports unmapped
tools. `source_ready` means those links exist. It does not prepare an environment,
execute a workflow, authorize a remote target or qualify a model.

| Recipe | Workflow | Independent verification |
| --- | --- | --- |
| web | Create/edit pages and use bounded browser actions | Actual desktop/phone views, interactions, layout and resources |
| writing | Write and revise constrained prose | Saved contents, requirements and separate content review |
| pdf | Build and inspect current PDF pages | Actual rendered pages, text/box checks and visual review |
| cad-plate | Build a fixed build123d plate | STEP reopen, geometry requirements and actual views |
| cad-components | Check the catalogue and runtime | M4 export/reopen and matching clearance-hole geometry |
| blender | Create a scene and animation | Reopened .blend, controlled views, motion and decoded video |
| remote-admin | Act on an explicitly configured owned target | Exact bytes, service checks and original-operation receipts |
| followup | Revise and recover original work | Current checks, preserved files and paired context/file identities |

## CAD and build123d

The graph separates environment readiness, coordinates/units, constraints,
sketches, solids, features, catalogue selection, components, plate, carrier and
measurement. Separate S³ difficulty cells and qualification remain necessary.

Existing BW setup pins build123d 0.13.0 and bd-warehouse 0.4.0, with a full lock
file. CAD construction and OSMesa views use the CPU. The operator supplies runtime
paths and fixed requirements before model work. Do not modify an admitted runtime
during a task. The candidate build does not receive the protected checker.

With an authorized model and the operator's prepared configuration:

```sh
branchwrite code /owned/project --project-files --cad-config /owned/cad-config.json --task-file /inspected/BW/examples/prompts/build123d.txt
```

That prompt uses the fixed plate family. Carrier interfaces have separate checks.
The component smoke is not an autonomous assembly-design pass. A plate checker
deliberately rejects unrequested hardware. Printed fit and general manufacturing
quality remain unproven.

## Blender

The graph separates environment, scenes, materials, transforms, animation,
rendering and video verification. Existing BW pins Blender 4.5.3 and MCP SDK
1.26.0 for its bounded stdio adapter. The operator supplies the runtime.

```sh
branchwrite code /owned/project --project-files --blender-config /owned/blender-config.json --task-file /inspected/BW/examples/prompts/blender.txt
```

Configuration fields are `distribution`, `mcp_python`, `timeout` and
`require_animation`. Existing fixtures use CPU Cycles and inspect actual outputs.
A Blender scene does not satisfy CAD acceptance. General arbitrary MCP and
arbitrary mixed-domain acceptance remain separate work.

If the model receives images, PCC needs a matching verified vision profile.
Human image review is a separately labeled assisted condition. A text-only model
must not receive credit for inspecting an image it never received.

## Instructions for the exploration model

1. Read the recipe, prerequisites, limits and historical evidence.
2. Confirm the operator-prepared environment and authorized resource window.
   Old paths, PIDs and example target names are not current permission.
3. Freeze the task, model/application profile and independent checks.
4. Invoke BW in an owned project and retain its returned state/export paths.
5. Inspect actual acceptance and artifacts. Preserve failures. Edits invalidate
   earlier checks; verify the latest source before claiming completion.
6. Reconcile uncertain effects using the original run and operation IDs.
7. Report the exact task, model, version and limits. One successful design is
   not general CAD, animation or administration mastery.

BW's `examples/prompts/results.json` preserves previous exact-prompt Q4 results
and their versions. S³ marks the new domain qualifications as planned while its
workflow registry identifies the existing implementation.

See BW's [spatial creation guide](https://github.com/CC-David-CC/BranchWrite/blob/main/SPATIAL-CREATION-GUIDE.md),
[workflow examples](https://github.com/CC-David-CC/BranchWrite/blob/main/examples/prompts/README.md),
[remote administration guide](https://github.com/CC-David-CC/BranchWrite/blob/main/docs/manual/10_REMOTE_ADMIN.md)
and [PDF guide](https://github.com/CC-David-CC/BranchWrite/blob/main/docs/manual/11_PDF_DOCUMENTS.md).

CPU checkpoint: [dated validation](../validation/foundations-20261023/README.md).
