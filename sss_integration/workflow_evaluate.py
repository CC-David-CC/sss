"""Run real BW tools against a leased native PCC/COW server, then grade outside it."""
import argparse
from contextlib import contextmanager
import json
import os
from pathlib import Path
import secrets
import threading

from sss.adapters.workflow_evaluation import BWWorkflowEvaluator
from sss.adapters.cow_evaluation import cow_gpu_admission,candidate_binding
from sss.adapters.cow_learning import write_once
from sss.workflow_assessment import create_project,make_launch,observe_capture
from sss.records import canonical,digest,file_sha256


@contextmanager
def native_server(panel,profile,output):
    from context_time_travel.real import BranchingModel
    from context_time_travel.llama_dense_backend import LlamaDenseBackend
    from context_time_travel.coordinator import ContextCoordinator
    from context_time_travel.pools import PoolConfig
    from serve.cow_adapter import CowAdapter
    from serve.cow_text_adapter import CowTextAdapter
    from serve.cow_grammar_disk import DurableGrammarCatalog
    from serve.cow_http import model_text_components,make_server
    from serve.cow_workspace import CowWorkspace
    cfg=panel.config
    with cow_gpu_admission(panel.pcc,profile,Path(profile['model_path']),profile['model_weights_sha256'],
            cfg['gpu_uuid'],context_tokens=cfg['context_tokens'],batch_tokens=cfg['batch_tokens'],
            stop_token_ids=cfg['stop_token_ids'],minimum_free_mib=cfg['minimum_free_mib'],
            maximum_initial_utilization=cfg['maximum_initial_utilization'],
            on_admission=lambda value:write_once(output/'admission.json',value)):
        store=output/'cow-store';components=model_text_components(profile['model_path'],
            dict(enable_thinking=False),model_contract_id=profile['model_contract_id'])
        coordinator=ContextCoordinator(store,PoolConfig(gpus=(cfg['gpu_index'],),
            ram_bytes=8*1024**3,disk_bytes=16*1024**3,min_available_bytes=4*1024**3),
            lambda gpu:BranchingModel(store,LlamaDenseBackend(profile,gpu_id=gpu),profile))
        server=thread=catalog=connection=None;old_key=os.environ.get('BW_COW_API_KEY')
        key=secrets.token_hex(24);os.environ['BW_COW_API_KEY']=key
        try:
            coordinator.ready();adapter=CowAdapter(coordinator)
            text=CowTextAdapter(adapter,**components)
            workspace=CowWorkspace(coordinator.store,text.tokenizer,
                root_mode_resolver=text.root_mode_for_projection)
            catalog=DurableGrammarCatalog(output/'grammars',text.tokenizer,profile['execution']['eos_tokens'])
            info=dict(model_contract_id=profile['model_contract_id'],
                execution_profile_id=profile['execution_profile_id'],eos_tokens=profile['execution']['eos_tokens'])
            server=make_server(adapter,api_key=key,text_adapter=text,workspace=workspace,
                grammar_catalog=catalog,connection_info=info)
            # Wait for all request handlers before retiring the leased model.
            server.daemon_threads=False;server.block_on_close=True
            thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            connection=dict(info,endpoint_url='http://127.0.0.1:'+str(server.server_port),
                endpoint_pin='sss-owned-workflow-'+panel.identity)
            write_once(output/'server-ready-private.json',dict(connection=connection))
            yield connection
        finally:
            if server is not None:server.shutdown();server.server_close()
            if thread is not None:thread.join(10)
            coordinator.close()
            if catalog is not None:catalog.close()
            if old_key is None:os.environ.pop('BW_COW_API_KEY',None)
            else:os.environ['BW_COW_API_KEY']=old_key
            if thread is not None and thread.is_alive():
                raise RuntimeError('Original workflow server thread has not retired')
            if connection is not None:
                write_once(output/'server-private.json',dict(status='RETIRED',connection=connection))


def run(owner_config,profile_path,candidate_path,output,*,expected_evaluator_id):
    from branchwrite.coding_cli import save_launch,run_saved
    from branchwrite.lesson_capture import capture_assessment
    from sss.adapters.bw_practice_oracle import observe
    panel=BWWorkflowEvaluator(owner_config)
    from sss.adapters.runtime_sources import require_child_identity
    require_child_identity(panel,expected_evaluator_id)
    read=lambda p:json.loads(Path(p).read_bytes())
    candidate=read(candidate_path);profile=read(profile_path)
    if canonical(panel.profile(candidate))!=canonical(profile):
        raise ValueError('Execution child differs from original workflow candidate')
    output=Path(output).absolute();output.mkdir(mode=0o700,exist_ok=False);rows=[]
    write_once(output/'intent-private.json',dict(evaluator_id=panel.identity,profile=profile,
        candidate=candidate,training=False))
    with native_server(panel,profile,output) as connection:
        for index,case in enumerate(panel.cases):
            folder=output/('%04d'%index);folder.mkdir(mode=0o700)
            create_project(case,folder/'project')
            launch=make_launch(case,folder/'project',connection,panel.config)
            save_launch(folder/'state',launch)
            returned=run_saved(folder/'state',max_steps=panel.config['maximum_steps'])
            write_once(folder/'runtime-result-private.json',returned)
            capture=capture_assessment(folder/'state',folder/'capture')
            workflow,source=observe_capture(case,capture,launch)
            proof=observe(case.case,source,workflow['source_sha256'],folder/'oracle')
            if proof['status']=='unavailable':
                raise RuntimeError('Independent checker unavailable; not a model failure')
            row=dict(id=case.identity,skill_id=case.skill_id,gate=case.gate,
                passed=workflow['finished'] and proof['status']=='pass',finished=workflow['finished'])
            write_once(folder/'observation-private.json',dict(outcome=row,workflow=workflow,oracle_status=proof['status']))
            rows.append(row)
    value=dict(schema=1,status='COMPLETE',evaluation_id=panel.evaluation_id,
        runtime_id=digest(panel.expected_runtime(profile)),model_sha256=profile['model_weights_sha256'],
        **candidate_binding(profile),cases=len(rows),passed=sum(r['passed'] for r in rows),
        finished=sum(r['finished'] for r in rows),outcomes=rows,evidence_directory=str(output.parent),
        weights_updated=False,promoted=False)
    panel._summary(value,candidate)
    write_once(output/'result.json',value)
    write_once(output/'settlement.json',dict(schema=1,status='COMPLETE',completed_cases=len(rows),
        result_sha256=file_sha256(output/'result.json'),weights_updated=False,promoted=False))
    return value


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('owner-config','profile','candidate','output'):
        parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--expected-evaluator-id',required=True)
    args=parser.parse_args()
    value=run(args.owner_config,args.profile,args.candidate,args.output,expected_evaluator_id=args.expected_evaluator_id)
    print(json.dumps({k:value[k] for k in ('status','cases','passed','finished')}))
