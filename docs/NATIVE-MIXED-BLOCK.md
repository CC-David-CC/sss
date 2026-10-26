# First mixed native block through BW and PCC

The learning machinery now executed one real full-model update through BW's
client, PCC's authenticated native job API and S³-verified lesson inputs.
It also preserved a named F32 GGUF privately. This proves a native job can consume
the verified mixed batch and save its candidate. It does not prove improvement:
the complete joined assessment still has an unresolved BW grammar-stream error.

## Plain-language reading

The machine practiced one code lesson and 27 arithmetic/state review lessons.
It changed the model and saved that version. Its loss on that very practice
batch rose, which is a reason to investigate, not to announce a better model.
The candidate is undergoing separate answer and retention measurements. Nothing
has been promoted or uploaded as model weights.

## Recorded measurements

| Item | Original record |
| --- | --- |
| Host | llm-60, RTX PRO 6000 Blackwell |
| Update | Ordinary native dense backprop, full AdamW, fresh moments |
| Presentations | One update, all 28 selected examples consumed |
| Review | Nine arithmetic/state skills, one example per mastery gate |
| Main learning-rate field | Approximately 0.00001 |
| Auxiliary learning-rate field in resolved native configuration | Approximately 0.0003 |
| Finite nonzero gradient tensors | 381 |
| Mean training loss before / after | 0.4197256 / 1.2127761 |
| Native terminal receipt | `MECHANICS_EXECUTED`, exit 0 |
| Native receipt's save/reload qualification flag | `false`; independent check queued separately |
| Preserved private file | `MiniCPM-S3-mixed-native01-full-F32.gguf` |
| Acceptance / publication of weights | Neither |

The [sanitized native receipt](../validation/learning-program-20261024/native-mixed-block-20261026.json)
retains model, job and preservation hashes. Full-mode rank 2 is an existing
request-schema field; this was a full update, not a rank-2 adapter. The resolved
auxiliary learning-rate field is reported explicitly. Its contribution to this
plain-AdamW result has not yet been established; it is not a diagnosed cause of
the loss increase. Nonzero gradients are not a new finite-difference gradient
check. A saved GGUF is not itself numerical save/reload qualification.

## What the BW attempt established

On the fresh protected target panel, the unchanged starting checkpoint produced
two correct artifacts and both responses naturally finished. In actual BW, the
first task completed `read_file`, `replace`, `read_file`, `run_check`, `finish`;
the independent artifact oracle also passed it.

On the second BW task the model tried to create a file that already existed.
The executor correctly refused that operation. The following attempted full-file
replacement repeated array entries across two settled 256-token response chunks.
A subsequent resume ended with an indeterminate grammar-stream error. The
original journal, completed first case, partial second case and retired server
records remain intact. This is incomplete workflow coverage, not an invented
0/2 score or a claim that every failure was model ignorance.

A CPU-only diagnostic on llm-49 replayed the 512 saved tokens through the exact
original grammar engine identity. Their masks and acceptance passed, including
the next mask calculation. This rules out a deterministic failure in that saved
prefix; it does not reproduce or explain the later failed resume. No model
question was redispatched for this diagnostic.

## Technical and applied interpretation

There are three separate questions: did native optimization execute, did the
candidate survive independent save/reload checks, and did measured behavior
improve without unacceptable forgetting? The first has evidence. The latter two
remain separate measurements. The native job was submitted independently after
the joined run stopped, using the exact already validated mixed lesson block;
the failed learning run was not rewritten into a success.

S³ owns lesson validation, frozen panels and comparisons. PCC owns model
identity, backprop, leases, jobs and immutable artifacts. BW supplies its actual
client journal and file/tool workflow. The 864-question new review before/after
panel and candidate artifact measurement are in flight at this snapshot. Its
completed baseline artifact responses are recovered from original evidence,
not generated again. An independent save/reload loss check waits for that
assessment owner to retire before acquiring the same worker/GPU leases.

The fixed ten-arm, 68-update optimizer/rank study is unchanged. This mixed block
is separate learning-loop qualification work, not an additional point on those
curves. No seed repeat, model transfer from A100, model upload or promotion was
performed. The joined observe/lesson/train/assess/decide/preserve pathway still
needs its workflow failure and complete acceptance/report behavior resolved.
