"""Regrade all original saved F32 case receipts without allocating a model."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,sys
h=Path.home();r=h/'wen-0.1.0/run/pcc-a100-parallel-curves-20261024-a';folder=r/'baseline-F32-development-c'
pcc=r/'inputs/pcc-tools';sss=r/'cow-testing-s/source/sss'
sys.path[:0]=[str(sss),str(pcc)]
from sss.records import digest
from sss.evaluation import implementation_identity
from sss.foundations import Exercise,check
from sss.paired import compare_frozen_evaluations,POLICY
from tools.strata_tokenizer import Tokenizer
from tools.gguf_reader import GGUFFile
read=lambda p:json.loads(p.read_bytes())
def sha(p):
 with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
result=read(folder/'result.json');intent=read(folder/'intent.json');settled=read(folder/'settlement.json')
data_path=r/'inputs/development-private.json';data=read(data_path)
assert sha(data_path)==intent['cases_sha256']
assert digest({k:v for k,v in data.items()if k!='evaluation_id'})==result['evaluation_id']==data['evaluation_id']
assert implementation_identity()==intent['runtime']['checker_implementation_id']
assert digest(intent['runtime'])==result['runtime_id']
assert result['status']==settled['status']=='COMPLETE'and result['cases']==settled['completed_cases']==864
compare_frozen_evaluations(result,result,POLICY)
for path,expected in intent['runtime']['runtime_artifacts'].items():assert sha(Path(path))==expected
model=Path('/dev/shm/sss-cs7375-dflanag3-curves-20261024-c/original-F32.gguf')
assert model.is_file()and sha(model)==result['model_sha256']=='2323c47d8bf14fb2906e1275688aa784768cf39a364729bc52bf6ba5c0742764'
metadata=GGUFFile(model).metadata
assert metadata['general.file_type']==0
tokenizer_id=digest(dict(metadata={k:v for k,v in metadata.items()if k.startswith('tokenizer.')},source_sha256=sha(pcc/'tools/strata_tokenizer.py')))
assert tokenizer_id==data['tokenizer_sha256']==intent['runtime']['tokenizer_sha256']
tok=Tokenizer.from_gguf(model);outcomes=[];hashes={}
for index,expected in enumerate(data['cases']):
 path=folder/(str(index).zfill(4)+'-private.json');row=read(path);exercise=Exercise(**expected['exercise'])
 assert row['index']==index and row['id']==exercise.identity==expected['exercise_id']
 assert row['model_sha256']==result['model_sha256']and row['runtime_id']==result['runtime_id']and row['evaluation_id']==result['evaluation_id']
 completion=row['completion'];tokens=completion['sampled_token_ids']
 assert type(tokens)is list and 1<=len(tokens)<=64 and all(type(i)is int and 0<=i<len(tok.tokens) for i in tokens)
 stopped=completion['stop_reason']=='eos'
 assert completion['stop_reason']in('eos','length')
 if stopped:
  assert tokens[-1]==completion['stop_token_id']and tokens[-1]in(1,130073)
 else:assert len(tokens)==64 and completion['stop_token_id']is None
 assert not any(t in(1,130073)for t in(tokens[:-1]if stopped else tokens))
 assert tok.decode(tokens[:-1]if stopped else tokens)==completion['text']
 assert row['passed']==check(exercise,completion['text'])and row['finished']==stopped
 outcomes.append({k:row[k]for k in ['id','skill_id','gate','passed','finished']});hashes[path.name]=sha(path)
assert outcomes==result['outcomes']
assert sum(v['passed']for v in outcomes)==result['passed']==59
assert sum(v['finished']for v in outcomes)==result['finished']==415
assert sha(data_path)==intent['cases_sha256']and sha(model)==result['model_sha256']
value=dict(schema=1,status='PASS',scope='All864existing original F32 receipts regraded/redecoded; no new inference',
 captured_utc=datetime.now(timezone.utc).isoformat(),format='F32',cases=864,correct=59,finished=415,
 bytes=model.stat().st_size,model_sha256=result['model_sha256'],runtime_id=result['runtime_id'],evaluation_id=result['evaluation_id'],
 scored_at_utc=datetime.fromtimestamp((folder/'result.json').stat().st_mtime,timezone.utc).isoformat(),
 evidence_sha256=sha(folder/'result.json'),case_receipts_sha256=digest(hashes),case_receipts=864,
 source_receipts_sha256={name:sha(folder/name)for name in ['result.json','settlement.json','intent.json']},
 checker_implementation_id=implementation_identity(),tokenizer_sha256=tokenizer_id,model_calls=0,training_updates=0,
 original_result_unchanged=True)
with(r/'original-f32-cases-cs-public.json').open('x')as f:json.dump(value,f,indent=2)
print(json.dumps(value))
