"""Prepare an actual-tokenizer S3 optimizer pilot; no GPU or native update."""
from pathlib import Path
import argparse,sys,json,hashlib
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--pcc-root',type=Path,required=True);p.add_argument('--model',type=Path,required=True);p.add_argument('--model-contract-id',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
pcc=a.pcc_root.resolve(strict=True);sys.path[:0]=[str(pcc),str(pcc/'experimental/branching_context/src')]
from serve.cow_http import model_text_components
from tools.gguf_reader import GGUFFile
from tools.pcc_lessons import LessonService
from sss.records import digest,file_sha256
from sss.adapters.pcc_foundation_render import PCCFoundationRenderer
from sss.adapters.optimizer_pilot import prepare
output=a.output.resolve();output.mkdir(mode=0o700,parents=True,exist_ok=False)
components=model_text_components(a.model,dict(enable_thinking=False),model_contract_id=a.model_contract_id)
tokenizer=components['tokenizer'];renderer=PCCFoundationRenderer(components)
metadata=GGUFFile(a.model).metadata
tokenizer_id=digest(dict(metadata={k:v for k,v in metadata.items() if k.startswith('tokenizer.')},source_sha256=file_sha256(pcc/'tools/strata_tokenizer.py')))
def no_training(*args):raise RuntimeError('Preparation grants no model update authority')
service=LessonService(output/'lesson-service',a.model_contract_id,lambda text:tokenizer.encode(text,parse_special=False),no_training,max_tokens=512,max_steps=3,sequence_profile='dense-llama-short-v1',rendered_tokenize=lambda text:tokenizer.encode(text,parse_special=True))
try:
 result=prepare(service,renderer,output/'prepared',tokenizer_sha256=tokenizer_id,model_sha256=file_sha256(a.model))
 print(json.dumps({k:result[k] for k in ['pilot_id','practice_lessons_admitted','protected_check_count','weights_updated']}))
 print(json.dumps(result['selection']))
finally:service.close()
