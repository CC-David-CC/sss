"""Parallel CPU collation of existing final precision evidence; no model calls."""
from pathlib import Path
from datetime import datetime,timezone
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import get_context
import hashlib,json,sys
root=Path.home()/'wen-0.1.0/run/pcc-a100-parallel-curves-20261024-a'
sys.path.insert(0,str(root/'cow-testing-s/source/sss'))
from sss.paired import compare_frozen_evaluations,POLICY
formats=['F32','F16','Q8_0','Q5_K_M','Q4_K_M','Q3_K_M','Q2_K','Q1_0']
studies={'muon-standard-full':'muon-standard-full-final-precision-cr','adamw-full':'adamw-full-final-precision-cn02','adamw-lora-r1':'rank1-final-precision-cn03',
 'adamw-lora-r2':'rank2-final-precision-cr','adamw-lora-r3':'rank3-final-precision-cl',
 'adamw-lora-r4':'rank4-final-precision-ck02','adamw-lora-r8':'rank8-final-precision-cr','adamw-lora-r16':'rank16-final-precision-cg',
 'muon-rms-decay-full':'muon-rms-decay-full-final-precision-cz','muon-fast-refine-full':'muon-fast-refine-full-final-precision-cz'}
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def collect(job):
 arm,fmt=job;study=root/studies[arm];folder=study/fmt
 pointer=folder/'explicit-recovery-pointer-private.json';recovery_pointer=None
 if pointer.exists():
  recovery_pointer=read(pointer)
  assert recovery_pointer['status']=='COMPLETE_VALIDATED_RECOVERY'
  assert recovery_pointer['completed_cases_repeated'] is False
  recovered=Path(recovery_pointer['directory'])
  known={('adamw-lora-r2','Q2_K'):'precision-relocation-cy',
   ('muon-standard-full','Q3_K_M'):'precision-relocation-cy',
   ('muon-fast-refine-full','Q2_K'):'precision-relocation-do'}
  assert (arm,fmt) in known, 'Unexpected recovery mapping'
  assert recovered.resolve()==(root/known[(arm,fmt)]/(studies[arm]+'-'+fmt)).resolve()
  assert sha(recovered/'summary.json')==recovery_pointer['summary_sha256']
  folder=recovered
 summary_path=folder/'summary.json'
 row=dict(arm=arm,format=fmt,status='PENDING',source_training_updates=68,source_presentations=1836)
 if not summary_path.exists():
  row['preserved_case_receipts']=len(list((folder/'development').glob('[0-9][0-9][0-9][0-9]-private.json')))
  row['claimed']=(folder/'claim-private.json').exists()
  return row
 reference=read(study/'F32/development/result.json')
 summary=read(summary_path);result=read(folder/'development/result.json');settlement=read(folder/'development/settlement.json')
 assert summary['status']==result['status']==settlement['status']=='COMPLETE'
 assert summary['cases']==result['cases']==settlement['completed_cases']==864
 for key in ['passed','finished','model_sha256','evaluation_id','runtime_id']:assert summary[key]==result[key]
 assert summary['reference_master_sha256']==reference['model_sha256']
 conversion=None;conversion_reuse=None
 if fmt!='F32':
  conversion_path=study/fmt/'conversion/result.json'
  if not conversion_path.exists():
   assert arm=='adamw-lora-r4', 'Unknown conversion-reuse source'
   reuse_path=study/fmt/'conversion-reuse-private.json';conversion_reuse=read(reuse_path)
   expected=(root/'rank4-final-precision-ck'/fmt/'conversion').resolve()
   assert Path(conversion_reuse['original_directory']).resolve()==expected
   assert conversion_reuse['conversion_repeated'] is False and conversion_reuse['original_preflight_failure_preserved'] is True
   assert conversion_reuse['model_sha256']==result['model_sha256']
   conversion_path=expected/'result.json'
   assert sha(conversion_path)==conversion_reuse['original_result_sha256']
  conversion=read(conversion_path)
  assert conversion['status']=='CONVERTED_NOT_EVALUATED'
  assert conversion['source_sha256']==reference['model_sha256']
  assert conversion['model_sha256']==result['model_sha256']
  assert conversion['requested_format']==fmt and conversion['bytes']==summary['bytes']

 paired=compare_frozen_evaluations(reference,result,POLICY)
 row.update(status='COMPLETE',cases=864,correct=result['passed'],finished=result['finished'],bytes=summary['bytes'],
  model_sha256=result['model_sha256'],reference_master_sha256=reference['model_sha256'],evaluation_id=result['evaluation_id'],runtime_id=result['runtime_id'],
  reference_reused=summary.get('original_evaluation_reused',False),
  **{key:paired[key]for key in ['answer_gains','answer_losses','completion_gains','completion_losses','groups']},
  source_receipts_sha256={name:sha(folder/name)for name in ['summary.json','development/result.json','development/settlement.json','cow-profile.json']})
 if conversion is not None:row['conversion_receipt_sha256']=sha(conversion_path)
 if conversion_reuse is not None:row.update(conversion_source_reused=True,conversion_reuse_receipt_sha256=sha(reuse_path))
 if recovery_pointer is not None:
  assert summary['recovery']==result['recovery']
  assert result['recovery']['completed_case_repeated'] is False and result['recovery']['native_update_repeated'] is False
  proof=read(folder/'source-records-private.json')
  assert len(proof)==864 and set(proof)=={str(i)for i in range(864)}
  outcomes=[]
  for index in range(864):
   original=proof[str(index)];path=Path(original['path']);assert sha(path)==original['sha256']
   value=read(path)
   outcomes.append({key:value[key]for key in ['id','skill_id','gate','passed','finished']})
  assert outcomes==result['outcomes'] and len({v['id']for v in outcomes})==864
  row.update(recovery=summary['recovery'],recovery_pointer_sha256=sha(pointer),
   recovery_source_map_sha256=sha(folder/'source-records-private.json'),original_failure_preserved=True)
 assert row['answer_gains']-row['answer_losses']==row['correct']-reference['passed']
 return row
if __name__=='__main__':
 with ProcessPoolExecutor(max_workers=4,mp_context=get_context('fork'))as pool:
  rows=list(pool.map(collect,[(arm,fmt)for arm in studies for fmt in formats]))
 value=dict(schema=1,status='COMPLETE'if all(r['status']=='COMPLETE'for r in rows)else'IN_PROGRESS',
  captured_utc=datetime.now(timezone.utc).isoformat(),scope='All ten frozen comparison arms; pending panels remain explicit',
  cases=864,training_updates=68,training_presentations=1836,rows=rows,analysis_processes=4,
  collector_sha256=sha(Path(__file__)),new_model_calls=0,new_training_updates=0,weights_published=False,promoted=False,
  timing_caveat='Shared A100 load; no isolated throughput claim')
 output=root/'final-checkpoint-precision-dp-public.json'
 with output.open('x')as f:json.dump(value,f,indent=2);f.write('\n')
 print(json.dumps(dict(status=value['status'],completed_points=sum(r['status']=='COMPLETE'for r in rows),
   pending=[dict(arm=r['arm'],format=r['format'],completed_cases=r.get('preserved_case_receipts',0))for r in rows if r['status']!='COMPLETE'])))
