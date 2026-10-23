# The skill graph on disk

Folders help people find a subject. Explicit prerequisite IDs determine what
must be mastered. A skill can have several parents and feed several branches.
Grade labels are navigation aids. They do not impose one universal difficulty
ladder or certify a complete school-grade curriculum.

```text
sss/
  catalog/
    skills/
      math/add/no_carry.json
      math/add/carry.json
      math/add/signed.json
      math/fraction/add.json
      math/percent/change.json
      logic/proof.json
      code/python/debug.json
      linux/services.json
      memory/compaction.json
      research/findings.json
      world/deadlines.json
    escalations/independent-axes-v1.json
    workflows/blender.json       existing BW recipe and checker/source pointers
    workflows/cad-plate.json
  catalogue.py          validates and loads these data files
  graph.py              validates dependency links and detects cycles
  foundations.py        exact generators and independent graders
  extended_math.py      fraction, decimal and percentage subskills
  suites/               tool and code task definitions
  adapters/             optional real runtime/environment connections
  mastery.py            frozen three-gate qualification and retention vetoes
  escalation.py         independent difficulty coordinates and recommendations
  curriculum.py         prerequisite-aware interleaved timetable selection
  episodes.py           immutable original episodes, notes, search and rereading
  research.py           reproducible computing-lab experiment fixture
  evaluation.py         frozen evaluation inputs and evidence-bound assessments
examples/
  profiles/             templates, without credentials
  finished-training-examples/  curated synthetic TXT conversations and manifests
```

Each skill JSON has a stable ID, plain title, subject labels, prerequisite IDs,
coverage bands, checker identity, generator binding, implementation status and a
coverage note. For example, `math.add.carry` requires `math.add.no_carry`.
`research.findings` converges experimentation, statistics and archived evidence.
The graph loader rejects missing parents, duplicate IDs, cycles and path/ID
mismatches. Moving a subject label does not silently change its prerequisites.

The escalation policy lists four independent axes: composition depth, context
tokens, environmental complexity and autonomy. Timing is separate. Their listed
values are curriculum coordinates, not evidence of implemented coverage. The
current `bounded-v1` math band supports small, explicit, self-contained problems.
Longer, more autonomous cells need their own working generator, checker and
frozen test suite before they can be enabled or qualified. `escalation.py`
recommends one-axis probes and refuses to treat unsupported cells as progress.

Each tested cell needs independent mastery, composition, and transfer/recovery.
The default qualification fixes 256 trials per gate. At least 251/256 must pass
in each gate to meet the declared exact-binomial bound; every declared critical
check and protected earlier success must also pass. A failed skill returns to
practice with retention work; changing the seed and repeatedly drawing until a
pass is not qualification. Scores apply to the declared distribution/profile,
not every ability in a subject or the entire graph.

Private generated runs live outside Git:

```text
YOUR_PRIVATE_RUN/
  frozen-private.json   exact model/modes, source identity, cases and suite hashes
  outcomes/             original requests, outputs, failures and evidence hashes
  assessment.json       per-gate counts, bounds, coverage and retention failures
YOUR_EPISODE_ARCHIVE/
  metadata.json
  events/00000000.json   immutable, ordered, source-linked original records
  compactions.json      causal working notes, never replacements for originals
  conversation.txt      readable complete teaching record
```

Evaluation inputs/answers never become practice by renaming a file. Public
examples are deliberately generated, independently checked synthetic practice.
Bulk archives, real traces, model weights and protected evaluations stay private.
Changing the catalog or scorer makes a different frozen evaluation version.
