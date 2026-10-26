# Continue a stopped BW workflow without starting its task over

S³ now provides an explicit recovery API and operator script for a stopped BW
case. It reopens the original PCC store, grammar catalog, loopback endpoint and
execution profile, and resumes the saved BW state. Completed requests and tool
effects are preserved. It does not create a replacement workflow ledger.

## Choose the recovery action explicitly

The helper first requires the original producer processes to be gone. Ordinary
reopening uses the original server's terminal receipt. BW's existing reconciler checks the
pending native frame, exact launch, source binding and journal.

If PCC proves that the original generation committed, the helper recovers that
answer without another forward pass. If commitment remains unknown, the default
is refusal. An owner can explicitly permit replay of the original generation ID
and bytes after producer exit, and only while the source branch still matches.
That replay can recompute unsettled native work. It is not proof that the first
attempt aborted, and it never retries a tool effect under a new ID.

The original source snapshot is important. The script verifies the original
evaluator ID, candidate and profile before dispatch. Use a qualified PCC runtime
that includes [grammar-completion replay metadata](https://github.com/CC-David-CC/Private_Context_COW/blob/fix/replay-grammar-metadata-20261026/docs/REPLAY-GRAMMAR-METADATA.md).
An older snapshot that lacks that metadata can still refuse a recovered complete
tool call. Source migration of old evaluators remains explicit work, not a
hidden change to their identities.

## Operator entry point

Run the new script while pointing it at the original installed sources and
evidence. These are example paths, not a complete deployment recipe:

```sh
python scripts/recover_bw_workflow.py \
  --sss-root /srv/run/original/sss --api-root /srv/run/original/api \
  --owner-config /srv/run/original/workflow-owner.json \
  --candidate /srv/run/panel/candidate-selection-private.json \
  --profile /srv/run/panel/candidate-profile.json \
  --evaluation /srv/run/panel/evaluation --case-index 0 \
  --output /srv/run/panel/evaluation/recovery-01 \
  --producer-owner /srv/run/original/controller-owner.json \
  --additional-steps 128 \
  --cache-bytes 17179869184 --staging-bytes 8589934592 \
  --minimum-free-bytes 4294967296
```

The recorded original child identity is mandatory and loaded automatically.
`--producer-owner` adds an outer controller identity. Add
`--allow-original-replay` only when intentionally authorizing that recovery
action. The default does not resend an unknown generation. The output directory
must be new; inspect a failed attempt before choosing another action.

If the server was killed before it could write its clean retirement receipt,
add `--adopt-crashed-server` explicitly. The helper requires the original
server-ready connection/profile, verifies the recorded producers have exited,
and probes that the original loopback endpoint can be bound. An occupied
endpoint refuses before model loading or GPU admission. It records a separate
crash-retirement proof and preserves the missing original shutdown receipt.
The replacement server must still bind normally; a new competing listener
causes refusal. This flag does not authorize replay of an unknown generation;
`--allow-original-replay` remains a separate selection.

The extra interpreter-step allowance is recorded separately. A recovered outcome
must not be presented as the original fixed-bound assessment or as model
promotion. The function API is `sss_integration.workflow_recovery.resume_case`.
The exact generic CLI was subsequently exercised on a new owned native probe
after deliberately killing its normal evaluator child. The
[native follow-up receipt](../validation/learning-program-20261024/unified-native-recovery-20261026.json)
records that qualification and its limited one-step continuation.

## Admit filesystem capacity before loading the model

The workflow server now checks filesystem headroom as well as the existing GPU
and RAM admission. `PoolConfig.min_available_bytes` is RAM headroom, not free disk.
Previously a 16-GiB disk-pool quota could exceed the physical space available.

The owner can supply a closed `storage` object in the workflow panel configuration:

```json
{
  "storage": {
    "cache_bytes": 17179869184,
    "staging_bytes": 8589934592,
    "minimum_free_bytes": 4294967296
  }
}
```

These are the current MiniCPM experiment's default allowances. Measure and choose
an appropriate native staging allowance for another model/context. Admission
requires free bytes for the remaining cache quota, staging and minimum reserve.
Existing checkpoint bytes are counted, and the check runs again after acquiring
the GPU lease. Other filesystem writers can still consume space; this check does
not reserve the whole shared filesystem or replace PCC's checkpoint accounting.

## Native observations and current limits

The [campaign receipt](../validation/learning-program-20261024/native-workflow-recovery-20261026.json)
records a native candidate02 case that completed read/edit/check/finish,
preserved its input and passed an independent code checker. Eighteen previously
completed operations stayed byte-identical. Its last generation was explicitly
replayed under its original ID after the storage failure, with 128 additional
interpreter steps available. Archival itself used no model calls.

The second case was attempted once. It used all eight response chunks and all
2,048 allowed output tokens without finishing its next tool action. All requests
settled. BW's read-only observer proves that budget failure; it is not a parser
crash, a completed correction or an independent artifact pass.

The initial disk-full failure was avoidable: the operator started the workflow
before the archival copy had completed. The original error is retained. The
failed candidate01 optimizer state was subsequently byte-verified and fsynced on
durable fleet storage before retiring its local copy, reclaiming 20,134,145,385
bytes. Model files and immutable job receipts were preserved; using that old
state now requires restoring its exact bytes to the recorded path first.

The [CPU qualification receipt](../validation/learning-program-20261024/workflow-recovery-controls-20261026.json)
covers durable and unsettled-send recovery, live-producer refusal, refusal without
explicit replay selection, filesystem admission before GPU lease, and actual
BW/PCC HTTP/ledger replay using a scripted CPU backend. No claim of a complete
joined learning round or same-bound optimizer/harness winner follows from this
campaign. Broader recovery coverage and the complete joined native learning
round remain open; the generic CLI's later native check is recorded below.

## A bounded unfinished turn is an assessment outcome

The standard workflow panel now records a proven `model_budget_exhausted`
outcome as `passed: false, finished: false` and continues to the next case.
BW verifies the frozen plan, complete native receipts and exhausted allowance;
a runtime status string alone is insufficient. An ordinary partial turn with
remaining allowance is refused. Infrastructure uncertainty still stops scoring.

BW archives the launch, ledger and request receipts under a read lease. The
archive excludes mutable world artifacts and native numerical caches. S³ can
reverify the failed boundary after the original workflow is moved or resumed,
without inference, tools or an invented artifact grade. This archive is private
assessment evidence, explicitly ineligible for training. Completed-turn lesson
capture remains a separate, stricter operation.

The expanded CPU qualification ran 33 checks across BW capture, S³ assessment
and recovery. A two-case scripted panel reached both cases, retained two bounded
failures, retired its server and produced a complete settlement. Reverification
used its archived bytes after the original states were moved; changed launch
bindings and tampered journal bytes were refused. The new reader also archived
and reverified the real native second-case failure with zero model/tool calls
and unchanged original ledger/journal bytes. This read-only qualification does
not claim a new native inference run through the updated generic panel or CLI.

## Native recovery after a real process death

The unified PCC checkout passed a bounded native COW branch smoke check using
the unchanged qualified native libraries. Its API and execution code came from
one source root; 19 native build files and 1,273 Python files were checked.

A new owned mechanics task then used the ordinary evaluator child command.
The operator deliberately killed only that child after its first native model
request was recorded as pending. The normal failed dispatch and absent clean
shutdown receipt were preserved. This is controlled infrastructure failure,
not a model-capability regression or a frozen comparison question.

The generic recovery CLI verified both producer exits and the old endpoint,
reopened the original store/profile, and explicitly replayed the same original
request ID. All three previously completed operations remained byte-identical.
It restored the model-turn boundary with one additional interpreter step and
retired its replacement server. Unsettled native work may have been recomputed;
no completed tool effect was resent.

The coding task remained unfinished and its original bad program failed the
independent checker. That result is retained. Recovery succeeded; this probe
does not establish a completed coding task, an improved model or a completed
learning round. No model training or weight publication occurred.

Recovery also supports an actually exhausted model budget: it archives the
proven failed boundary and returns failed/unfinished without admitting a partial
turn as a lesson. Fifteen CPU checks cover assessment, original-request recovery,
crash adoption/refusal, occupied endpoints and bounded-failure settlement.

## Closed unverified attempts

A supported workflow can terminate with a recorded false verdict after changing
files but never establishing a current checked finish. S3 now consumes BW's
separate terminal-failure archive for this boundary in ordinary panels and the
explicit recovery helper. It records passed=false and finished=false, with
artifact correctness unassessed. It neither fabricates an oracle result nor
turns this failure into a verified lesson. Model-budget exhaustion remains a
separate proven boundary; unsettled or unsupported effects remain unavailable.

The [qualification](../validation/learning-program-20261024/terminal-workflow-failure-20261026.json)
records the actual native read-only observation and 39 CPU controls across BW
and S3. A two-case scripted CPU panel continues after both terminal failures,
and revalidates their archives without the original world or server. These are
machinery checks, not a measured model improvement. The original joined native
baseline remains stopped and unchanged; complete joined train/assess/decision
qualification is still open. A changed source installation needs its own bound
policy and evidence, rather than relabelling an old failed evaluator as passed.
