"""Explicit owner recovery of a stopped BW workflow, using its original runtime.

No training, replacement workflow ledger or automatic retry of tool effects.
This module can be loaded by file path while the original S3/BW/PCC snapshot
remains on sys.path. Recovery therefore need not rewrite an evaluator's sources.
"""
from contextlib import contextmanager
from pathlib import Path
import hashlib
import json
import os
import secrets
import shutil
import socket
import threading
from urllib.parse import urlsplit

from sss.adapters.cow_learning import write_once,process_identity
from sss.records import canonical,file_sha256

DEFAULT_STORAGE=dict(cache_bytes=16<<30,staging_bytes=8<<30,minimum_free_bytes=4<<30)

def storage_policy(config):
    value=config.get('storage',DEFAULT_STORAGE)
    if type(value)is not dict or set(value)!=set(DEFAULT_STORAGE)or any(type(v)is not int or v<=0 for v in value.values()):
        raise ValueError('Closed positive workflow storage allowances required')
    return dict(value)

def require_retired(identities):
    if not identities:raise ValueError('Original producer identities are required')
    for identity in identities:
        if (type(identity)is not dict or set(identity)!={'pid','start_ticks','boot_id'}
                or type(identity['pid'])is not int or identity['pid']<=0):
            raise ValueError('Exact original producer identity required')
        try:current=process_identity(identity['pid'])
        except FileNotFoundError:continue
        if current==identity:raise ValueError('Original producer is still present; no replay')

def storage_admission(directory,*,cache_bytes,staging_bytes,minimum_free_bytes):
    """Check filesystem capacity, distinct from PoolConfig's RAM headroom.

    The owner declares the disk pool and native staging allowance. This bounds
    this pool's further allocation; unrelated writers can still consume space.
    """
    directory=Path(directory).resolve(strict=True)
    for value in (cache_bytes,staging_bytes,minimum_free_bytes):
        if type(value)is not int or value<=0:raise ValueError('Positive explicit filesystem allowances required')
    used=0;checkpoints=directory/'cow-store/checkpoints'
    if checkpoints.exists():
        if checkpoints.is_symlink()or not checkpoints.is_dir():raise ValueError('Invalid owned checkpoint directory')
        for path in checkpoints.iterdir():
            if path.is_symlink():raise ValueError('Checkpoint symlink is not an owned cache')
            if path.is_file():used+=path.stat().st_size
    free=shutil.disk_usage(directory).free
    required=max(0,cache_bytes-used)+staging_bytes+minimum_free_bytes
    if free<required:
        raise ValueError('Workflow filesystem admission refused: available '+str(free)+' bytes, required '+str(required))
    return dict(schema=1,available_bytes=free,required_free_bytes=required,
        existing_checkpoint_bytes=used,cache_bytes=cache_bytes,
        staging_bytes=staging_bytes,minimum_free_bytes=minimum_free_bytes)

@contextmanager
def reopened_server(panel,profile,evaluation,recovery,*,storage,
                    allow_crashed_server=False,producer_identities=()):
    """Reopen the original store, grammar catalog, endpoint and profile."""
    from sss.adapters.cow_evaluation import cow_gpu_admission
    from context_time_travel.real import BranchingModel
    from context_time_travel.llama_dense_backend import LlamaDenseBackend
    from context_time_travel.coordinator import ContextCoordinator
    from context_time_travel.pools import PoolConfig
    from serve.cow_adapter import CowAdapter
    from serve.cow_text_adapter import CowTextAdapter
    from serve.cow_grammar_disk import DurableGrammarCatalog
    from serve.cow_http import model_text_components,make_server
    from serve.cow_workspace import CowWorkspace
    cfg=panel.config;evaluation=Path(evaluation);recovery=Path(recovery)
    if type(allow_crashed_server)is not bool:raise ValueError('Explicit crashed-server adoption selection required')
    terminal=evaluation/'server-private.json';missing=not terminal.exists()
    if missing:
        if not allow_crashed_server:
            raise ValueError('Original server has no terminal receipt; explicit crashed-server adoption required')
        require_retired(producer_identities)
        ready=evaluation/'server-ready-private.json';original=json.loads(ready.read_bytes())
        if type(original)is not dict or set(original)!={'connection'}:
            raise ValueError('Original server-ready receipt is invalid')
    else:
        original=json.loads(terminal.read_bytes())
        if original['status']!='RETIRED':raise ValueError('Original server has no terminal receipt')
    connection=original['connection'];parsed=urlsplit(connection['endpoint_url'])
    if (parsed.scheme!='http'or parsed.hostname!='127.0.0.1'or not parsed.port
            or parsed.path or parsed.query or parsed.fragment):raise ValueError('Original loopback endpoint required')
    for name in ('model_contract_id','execution_profile_id'):
        if connection[name]!=profile[name]:raise ValueError('Original server profile changed')
    if connection['eos_tokens']!=profile['execution']['eos_tokens']:raise ValueError('Original EOS policy changed')
    if missing:
        # Match the HTTP server's reuse-address policy. A live listener still
        # prevents binding; no socket or port is taken away from another owner.
        require_retired(producer_identities)
        try:
            with socket.socket()as probe:
                probe.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
                probe.bind(('127.0.0.1',parsed.port))
        except OSError as exc:
            raise ValueError('Original loopback endpoint is still in use; no crashed-server adoption')from exc
        write_once(recovery/'crashed-server-retirement-private.json',dict(schema=1,
            original_terminal_receipt_missing=True,server_ready_sha256=file_sha256(ready),
            original_producer_identities=producer_identities,endpoint_bind_probe_succeeded=True,
            original_receipts_rewritten=False,scope='Explicit producer-exit and endpoint proof; not an original clean shutdown receipt'))
    admission=storage_admission(evaluation,**storage)
    write_once(recovery/'filesystem-admission-private.json',admission)
    server=thread=catalog=coordinator=None;prior_key=os.environ.get('BW_COW_API_KEY')
    with cow_gpu_admission(panel.pcc,profile,Path(profile['model_path']),profile['model_weights_sha256'],
            cfg['gpu_uuid'],context_tokens=cfg['context_tokens'],batch_tokens=cfg['batch_tokens'],
            stop_token_ids=cfg['stop_token_ids'],minimum_free_mib=cfg['minimum_free_mib'],
            maximum_initial_utilization=cfg['maximum_initial_utilization'],
            on_admission=lambda value:write_once(recovery/'gpu-admission-private.json',value)):
        # Recheck after taking the existing GPU lease, before loading the model.
        storage_admission(evaluation,**storage)
        try:
            store=evaluation/'cow-store'
            components=model_text_components(profile['model_path'],dict(enable_thinking=False),model_contract_id=profile['model_contract_id'])
            coordinator=ContextCoordinator(store,PoolConfig(gpus=(cfg['gpu_index'],),
                ram_bytes=8*1024**3,disk_bytes=storage['cache_bytes'],min_available_bytes=4*1024**3),
                lambda gpu:BranchingModel(store,LlamaDenseBackend(profile,gpu_id=gpu),profile))
            coordinator.ready();adapter=CowAdapter(coordinator);text=CowTextAdapter(adapter,**components)
            workspace=CowWorkspace(coordinator.store,text.tokenizer,root_mode_resolver=text.root_mode_for_projection)
            catalog=DurableGrammarCatalog(evaluation/'grammars',text.tokenizer,profile['execution']['eos_tokens'])
            key=secrets.token_hex(24);os.environ['BW_COW_API_KEY']=key
            info={name:connection[name]for name in ('model_contract_id','execution_profile_id','eos_tokens')}
            server=make_server(adapter,port=parsed.port,api_key=key,text_adapter=text,workspace=workspace,grammar_catalog=catalog,connection_info=info)
            server.daemon_threads=False;server.block_on_close=True
            thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            write_once(recovery/'server-ready-private.json',dict(connection=connection))
            yield connection
        finally:
            if server is not None:server.shutdown();server.server_close()
            if thread is not None:thread.join(10)
            if coordinator is not None:coordinator.close()
            if catalog is not None:catalog.close()
            if prior_key is None:os.environ.pop('BW_COW_API_KEY',None)
            else:os.environ['BW_COW_API_KEY']=prior_key
            if thread is not None and thread.is_alive():raise RuntimeError('Recovery server is still alive')
            if thread is not None:write_once(recovery/'server-retired-private.json',dict(status='RETIRED',connection=connection))

def resume_case(panel,profile,candidate,evaluation,index,recovery,*,producer_identities,
                additional_steps,allow_original_replay,storage,allow_crashed_server=False):
    """Explicit continuation; additional step allowance is recorded separately."""
    from branchwrite.coding_cli import read_launch,run_saved,_client
    from branchwrite.coding_reconciliation import reconcile_saved
    from branchwrite.model_dispatch import ModelReconciliationRequired
    from branchwrite.cow_client import COWSourceBinding,OperationIndeterminate
    from branchwrite.records import RuntimeLog
    from branchwrite.lesson_capture import capture_assessment
    from sss.workflow_assessment import make_launch,observe_capture
    from sss.adapters.bw_practice_oracle import observe
    require_retired(producer_identities);panel.verify()
    if type(additional_steps)is not int or not 1<=additional_steps<=1024:raise ValueError('Explicit additional interpreter steps required')
    if type(allow_original_replay)is not bool:raise ValueError('Explicit replay selection required')
    if type(allow_crashed_server)is not bool:raise ValueError('Explicit crashed-server adoption selection required')
    if canonical(panel.profile(candidate))!=canonical(profile):raise ValueError('Original candidate/profile changed')
    evaluation=Path(evaluation).resolve(strict=True);folder=evaluation/('%04d'%index);state=folder/'state'
    if (folder/'observation-private.json').exists():raise ValueError('Case already has an outcome; do not rerun it')
    launch=read_launch(state);recovery=Path(recovery);recovery.mkdir(mode=0o700,exist_ok=False)
    completed={p.name:file_sha256(p)for p in(state/'cow-operations').glob('*.json')
        if json.loads(p.read_bytes()).get('state')=='complete'}
    pending=[json.loads(p.read_bytes())for p in(state/'cow-operations').glob('*.json')
        if json.loads(p.read_bytes()).get('state')=='pending']
    if len(pending)!=1:raise ValueError('Exactly one original pending operation is required')
    record=pending[0];operation=record['operation_id']
    if record.get('method')!='POST'or record.get('path')not in('/cow/text/answer','/cow/text/ask','/cow/text/resume','/cow/text/append-user'):
        raise ValueError('Recovery is restricted to original model generation, never a tool effect')
    write_once(recovery/'intent-private.json',dict(schema=1,evaluator_id=panel.identity,
        original_operation_id=operation,original_record_sha256=record['record_sha256'],
        original_producer_identities=producer_identities,completed_operation_sha256=completed,
        additional_interpreter_steps=additional_steps,original_replay_explicitly_allowed=allow_original_replay,
        crashed_server_adoption_explicitly_allowed=allow_crashed_server,
        original_failed_child_unchanged=True,is_original_fixed_bound_assessment=False))
    replayed=False
    with reopened_server(panel,profile,evaluation,recovery,storage=storage,
            allow_crashed_server=allow_crashed_server,producer_identities=producer_identities)as connection:
        if canonical(make_launch(panel.cases[index],folder/'project',connection,panel.config))!=canonical(launch):
            raise ValueError('Original launch changed')
        client=_client(state,launch)
        # The normal BW reconciler validates the exact waiting native frame,
        # source binding, frozen launch and journal under a ledger read lease.
        with RuntimeLog(state/'ledger',read_only=True):
            try:reconcile_saved(state,operation)
            except ModelReconciliationRequired:
                if not allow_original_replay:raise
                try:observation=client.operation(operation)
                except OperationIndeterminate as exc:
                    if str(exc)!='COW operation is unknown in this process; commit state is indeterminate':raise
                    observation=None
                if observation is not None:raise ValueError('A current coordinator still owns the operation; no replay')
                binding=COWSourceBinding.from_json(record['source_binding']);head=client.head(binding.branch)
                if (binding.branch!=binding.source_branch or head.revision!=binding.revision or head.tip!=binding.snapshot):
                    raise ValueError('Original source head changed; do not resubmit')
                require_retired(producer_identities)
                write_once(recovery/'explicit-original-replay-private.json',dict(operation_id=operation,
                    body_sha256=record['body_sha256'],source_binding=binding.to_json(),
                    may_recompute_unsettled_native_work=True,not_proof_of_abort=True,
                    new_operation_id_created=False,tool_effect_replay=False))
                client.replay_original(operation);replayed=True
                reconcile_saved(state,operation)
        returned=run_saved(state,max_steps=additional_steps)
        write_once(recovery/'runtime-result-private.json',returned)
        if (type(returned)in(list,tuple)and len(returned)==2 and type(returned[1])is dict
                and returned[1].get('status')=='model_budget_exhausted'):
            from branchwrite.coding_observation import archive_model_budget
            from sss.workflow_assessment import observe_budget
            archive_model_budget(state,recovery/'budget')
            observed=observe_budget(panel.cases[index],recovery/'budget',launch)
            workflow=dict(observed['budget'],budget_archive_id=observed['budget_archive_id'],finished=False)
            oracle_status=observed['oracle_status'];passed=False
        else:
            capture=capture_assessment(state,recovery/'capture')
            workflow,source=observe_capture(panel.cases[index],capture,launch)
            oracle=observe(panel.cases[index].case,source,workflow['source_sha256'],recovery/'oracle')
            if oracle['status']=='unavailable':raise RuntimeError('Independent checker unavailable')
            oracle_status=oracle['status'];passed=workflow['finished']and oracle_status=='pass'
        for name,expected in completed.items():
            if file_sha256(state/'cow-operations'/name)!=expected:raise ValueError('Previously completed operation changed')
        result=dict(schema=1,kind='sss.explicit-workflow-recovery.v1',case_id=panel.cases[index].identity,
            candidate_sha256=profile['model_weights_sha256'],original_operation_id=operation,
            finished=workflow['finished'],passed=passed,
            original_operation_replayed=replayed,completed_operations_preserved=len(completed),
            additional_interpreter_steps=additional_steps,workflow=workflow,oracle_status=oracle_status,
            model_weights_updated=False,promoted=False,is_original_fixed_bound_assessment=False)
        write_once(recovery/'result-private.json',result)
    return result
