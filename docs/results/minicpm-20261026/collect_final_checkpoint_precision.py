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
studies={'adamw-full':'adamw-full-final-precision-cn02','adamw-lora-r1':'rank1-final-precision-cn03',
 'adamw-lora-r2':'rank2-final-precision-cr','adamw-lora-r3':'rank3-final-precision-cl',
 'adamw-lora-r4':'rank4-final-precision-ck02','adamw-lora-r8':'rank8-final-precision-cr','adamw-lora-r16':'rank16-final-precision-cg'}
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def collect(job):
 arm,fmt=job;study=root/studies[arm];folder=study/fmt;summary_path=folder/'summary.json'
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
 paired=compare_frozen_evaluations(reference,result,POLICY)
 row.update(status='COMPLETE',cases=864,correct=result['passed'],finished=result['finished'],bytes=summary['bytes'],
  model_sha256=result['model_sha256'],reference_master_sha256=reference['model_sha256'],evaluation_id=result['evaluation_id'],runtime_id=result['runtime_id'],
  reference_reused=summary.get('original_evaluation_reused',False),
  **{key:paired[key]for key in ['answer_gains','answer_losses','completion_gains','completion_losses','groups']},
  source_receipts_sha256={name:sha(folder/name)for name in ['summary.json','development/result.json','development/settlement.json','cow-profile.json']})
 assert row['answer_gains']-row['answer_losses']==row['correct']-reference['passed']
 return row
if __name__=='__main__':
 with ProcessPoolExecutor(max_workers=4,mp_context=get_context('fork'))as pool:
  rows=list(pool.map(collect,[(arm,fmt)for arm in studies for fmt in formats]))
 value=dict(schema=1,status='COMPLETE'if all(r['status']=='COMPLETE'for r in rows)else'IN_PROGRESS',
  captured_utc=datetime.now(timezone.utc).isoformat(),scope='Final full AdamW and all six standalone LoRA ranks; Muon precision sweeps separate',
  cases=864,training_updates=68,training_presentations=1836,rows=rows,analysis_processes=4,
  collector_sha256=sha(Path(__file__)),new_model_calls=0,new_training_updates=0,weights_published=False,promoted=False,
  timing_caveat='Shared A100 load; no isolated throughput claim')
 output=root/'final-checkpoint-precision-cr02-public.json'
 with output.open('x')as f:json.dump(value,f,indent=2);f.write('\n')
 print(json.dumps(dict(status=value['status'],completed_points=sum(r['status']=='COMPLETE'for r in rows),
   pending=[dict(arm=r['arm'],format=r['format'],completed_cases=r.get('preserved_case_receipts',0))for r in rows if r['status']!='COMPLETE'])))
