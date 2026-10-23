# References and extraction record

## tool-eval-bench

Reference: <https://github.com/SeraphimSerapis/tool-eval-bench>

Inspected revision: `c3d256aff55eebe981345a832eb6d1eea340763c`.
Its root LICENSE is MIT, copyright 2026 SeraphimSerapis. The implementation and
methodology were inspected as design references. No upstream executable package
or scenario answers are bundled in SÂ³'s training data.

The concepts informing the original file-tool suite are tool selection,
parameter precision, dependency chains, read-before-write, recovery, state,
scope and truthful completion. The nine current SÂ³ scenarios use new fixtures
and host-trace graders. They are not a claim to reproduce the upstream score or
to port its entire scenario catalog.

The reference benchmark primarily observes conversations with deterministic mock
tools. SÂ³ distinguishes that evidence from real BW filesystem/process execution,
native learning mechanics, model answer quality and whole-task administration.

## PCC and BW extraction

The arithmetic study/checker originates in PCC development through commit
`1b8b0b236d16d9584e028c5e106ee47ac2e1fd63`. The first skill guard/tree was new
uncommitted development in the same worktree, extracted here before publication.
BW lesson integration originates in development through
`cc7ba461e276c83a9f92009ed65aab8b06ac2c1f`; shared integration fixtures now live
in the SÂ³ adapter/test package.

PCC retains native backprop and resource ownership. BW retains its canonical
workflow ledger, host checks, tools and lesson-authoring evidence. Thin imports
preserve the earlier optional PCC study entry points. SÂ³ is a separate package
and repository, rather than another copy of those runtimes.
