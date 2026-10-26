"""Execute a protected artifact panel through existing COW and BW primitives."""
import argparse
import json
from pathlib import Path

from sss.adapters.artifact_evaluation import CowArtifactEvaluator
from sss.adapters.cow_learning import write_once
from sss.adapters.cow_evaluation import cow_session,token_completion,candidate_binding
from sss.adapters.bw_verified_practice import _extract
from sss.adapters.bw_practice_oracle import observe
from sss.records import canonical,digest,file_sha256


def run(owner_config,profile_path,candidate_path,output,*,expected_evaluator_id):
    panel=CowArtifactEvaluator(owner_config)
    from sss.adapters.runtime_sources import require_child_identity
    require_child_identity(panel,expected_evaluator_id)
    read=lambda p:json.loads(Path(p).read_bytes())
    candidate=read(candidate_path);profile=read(profile_path)
    if canonical(panel.profile(candidate))!=canonical(profile):
        raise ValueError('Execution child profile differs from exact original candidate')
    output=Path(output).absolute();output.mkdir(mode=0o700,exist_ok=False)
    rows=[];cfg=panel.config
    write_once(output/'intent-private.json',dict(evaluator_id=panel.identity,profile=profile,
        prefixes_sha256=digest(panel.prefixes),candidate=candidate,training=False))
    with cow_session(panel.pcc,profile,Path(profile['model_path']),profile['model_weights_sha256'],
            cfg['gpu_uuid'],output,context_tokens=cfg['context_tokens'],batch_tokens=cfg['batch_tokens'],
            stop_token_ids=cfg['stop_token_ids'],minimum_free_mib=cfg['minimum_free_mib'],
            maximum_initial_utilization=cfg['maximum_initial_utilization'],
            on_admission=lambda value:write_once(output/'admission.json',value)) as session:
        write_once(output/'shared-prefix.json',session.prepare_shared_prefix(panel.prefix))
        for index,(case,prefix) in enumerate(zip(panel.cases,panel.prefixes)):
            completion=token_completion(session,panel.decoder,prefix,maximum=cfg['maximum_tokens'],
                stop_token_ids=cfg['stop_token_ids'],stream='artifact-'+case.identity)
            parsed='invalid';passed=False
            try:source=_extract(completion['text'],case.source_mode)
            except (ValueError,UnicodeError):pass
            else:
                parsed='valid'
                import hashlib
                proof=observe(case.case,source,hashlib.sha256(source).hexdigest(),output/('oracle-%04d'%index))
                if proof['status']=='unavailable':
                    raise RuntimeError('Independent artifact checker unavailable; not a model failure')
                passed=proof['status']=='pass'
            row=dict(id=case.identity,skill_id=case.skill_id,gate=case.gate,passed=passed,
                     finished=completion['stop_reason']=='eos')
            write_once(output/('%04d-private.json'%index),dict(outcome=row,completion=completion,
                prefix_sha256=digest(prefix),artifact_parse=parsed))
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
