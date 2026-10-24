# LearnHarness as a design reference

Inspected the source at revision 6cba9c8c5afe8a63f47ea4ebae6e91d8a205cebb. This was a read-only review on an
owner-authorized development host. No upstream application, agent, dependency
install or model request was executed. This is design evidence, not a benchmark
of its teaching effectiveness. The repository declares AGPL-3.0; no source code
or training examples were copied into S3, BW or PCC.

## Useful distinctions in the implementation

The session plan is a prerequisite DAG. Its arrows say what a lesson depends on.
The persistent knowledge representation stores propositions and reasoning chains:
a chain groups premises jointly leading to one conclusion. Two independent
arguments for the same conclusion remain separate. The canvas is derived from
these records; it is not the authoritative reasoning store.

Sources: [graph contracts](https://github.com/amosblomqvist/learnharness/blob/6cba9c8c5afe8a63f47ea4ebae6e91d8a205cebb/src/core/contracts/graph.ts),
[graph derivation](https://github.com/amosblomqvist/learnharness/blob/6cba9c8c5afe8a63f47ea4ebae6e91d8a205cebb/src/core/graph.ts), and
[plan status implementation](https://github.com/amosblomqvist/learnharness/blob/6cba9c8c5afe8a63f47ea4ebae6e91d8a205cebb/src/core/contracts/plan.ts).

The plan's current/visited/upcoming labels derive from question calls, not answer
success. In particular, moving on after an incorrect answer still marks a topic
visited. The knowledge graph intentionally does not store mastery scores.
S3 must continue to derive skill claims from independent checks, including
composition, transfer/recovery and preserved earlier successes.

The extraction pipeline uses a language model to propose claims and another
stage to identify existing propositions. Its structural checks validate IDs,
nonempty premises and direct self-reference. These checks do not independently
prove arbitrary natural-language entailments or the truth of a proposition.
S3 needs explicit assumptions, source evidence, checker identities and unresolved
status before treating a proposed reasoning chain as a verified teaching target.

Source: [extraction pipeline](https://github.com/amosblomqvist/learnharness/blob/6cba9c8c5afe8a63f47ea4ebae6e91d8a205cebb/src/agent/subagents/extraction.ts).

## Concrete additions worth testing in S3

| Idea | Proposed use | Evidence needed |
| --- | --- | --- |
| Joint premises and alternate arguments | Preserve the exact dependency structure of a worked lesson | Independent verification of the claimed conclusion from the stated assumptions |
| Discrimination practice | Present near-matching problems that require different methods | Unseen cases where cues cannot substitute for choosing the correct operation |
| Reverse questions | Ask which conditions could justify a result | Grader accepts valid alternatives and rejects unjustified converse reasoning |
| Remove or weaken a premise | Ask whether a conclusion still follows, or request a counterexample | Exact proof/counterexample checker for the bounded family |
| Delayed, interleaved retrieval | Revisit a skill after other subjects and archive compaction | Distinguish unassisted recall, archive lookup and assisted correction |
| Source-linked graph views | Let an operator open the original lesson, failure and test receipt | Original immutable evidence remains available after summaries change |

Source: [practice design](https://github.com/amosblomqvist/learnharness/blob/6cba9c8c5afe8a63f47ea4ebae6e91d8a205cebb/src/agent/prompts/practice/10-doctrine.md).
The prompt's statements about learning mechanisms and preferred success rates
are hypotheses for our setting, not established Wen/Codi training facts.

## Fit with the existing projects

S3 already owns a prerequisite graph and assessment evidence. A reasoning graph
would describe arguments inside lessons and research episodes; it must not merge
skill prerequisites, logical implication and empirical support into one
unlabelled relation. Raw failed attempts, contrary evidence and later corrections
remain in the original episode archive even when the displayed explanation is
revised. A model-written explanation is not automatically a verified target.

BW continues to own execution and its task ledger; PCC continues to own contexts,
weights and native training. Use source-linked read-only graph views and original
bounded problem generators rather than introduce another agent runtime.

The first implementation now supplies four original bounded families and an
interleaved archive-reread fixture through existing S3/BW interfaces. See the
[reasoning curriculum](REASONING-CURRICULUM.md) for exact coverage, commands and
limits. The independent full-update campaign keeps its original frozen packs;
these additions do not retrospectively change its tests or establish model gains.
