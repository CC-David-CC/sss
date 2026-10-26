"""Read a completed precision panel; validate original paired evidence, never run it.

Run with the panel's S3 checkout on PYTHONPATH. Output contains aggregate counts
and evidence hashes only, not protected questions, responses or filesystem paths.
"""
import argparse
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone
from sss.paired import compare_frozen_evaluations, POLICY

FORMATS=('F16','Q8_0','Q5_K_M','Q4_K_M','Q3_K_M','Q2_K','Q1_0')

def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()

def read(path):return json.loads(Path(path).read_bytes())

def collect(root,reference):
    root=Path(root);reference=Path(reference)
    base=read(reference/'development/result.json')
    settlement=read(reference/'development/settlement.json')
    compare_frozen_evaluations(base,base,POLICY)
    assert base['status']==settlement['status']=='COMPLETE'
    assert base['cases']==settlement['completed_cases']==864
    rows=[];proof=[]
    for fmt in FORMATS:
        directory=root/fmt;summary=read(directory/'summary.json')
        actual=Path(summary.get('evaluation_directory',directory/'development'))
        result=read(actual/'result.json');settled=read(actual/'settlement.json')
        delta=compare_frozen_evaluations(base,result,POLICY)
        assert summary['status']==result['status']==settled['status']=='COMPLETE'
        assert summary['cases']==result['cases']==settled['completed_cases']==864
        assert summary['model_sha256']==result['model_sha256']
        assert summary['source_model_sha256']==base['model_sha256']
        assert summary['runtime_id']==result['runtime_id']==base['runtime_id']
        assert summary['evaluation_id']==result['evaluation_id']==base['evaluation_id']
        for k in ('passed','finished'):assert summary[k]==result[k]
        for k in ('answer_gains','answer_losses','completion_gains','completion_losses'):
            assert summary[k]==delta[k]
        assert summary['new_training'] is summary['promoted'] is summary['weights_updated'] is False
        rows.append(summary)
        proof.append(dict(format=fmt,result_sha256=sha(actual/'result.json'),
            settlement_sha256=sha(actual/'settlement.json'),summary_sha256=sha(directory/'summary.json'),
            **{k:summary[k] for k in ('cases','passed','finished','answer_gains','answer_losses')}))
    exemplar=rows[0]
    reference_row=dict(format='F32',status='COMPLETE',reference_format='F32',
        checkpoint=exemplar['checkpoint'],update=exemplar['update'],
        training_presentations=exemplar['training_presentations'],
        model_sha256=base['model_sha256'],source_model_sha256=base['model_sha256'],
        **{k:base[k] for k in ('cases','passed','finished','runtime_id','evaluation_id')},
        answer_gains=0,answer_losses=0,completion_gains=0,completion_losses=0,
        new_training=False,promoted=False,weights_updated=False)
    receipt=dict(schema=1,kind='sss.trained-precision-paired-validation.v1',status='PASS',
        captured_utc=datetime.now(timezone.utc).isoformat(),checkpoint=exemplar['checkpoint'],
        reference_model_sha256=base['model_sha256'],
        reference_result_sha256=sha(reference/'development/result.json'),
        reference_settlement_sha256=sha(reference/'development/settlement.json'),
        reference_runtime_id=base['runtime_id'],evaluation_id=base['evaluation_id'],
        validator_source_sha256=sha(compare_frozen_evaluations.__code__.co_filename),
        collector_source_sha256=sha(__file__),formats=proof)
    return dict(schema=1,rows=[reference_row]+rows,validation=receipt)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--reference',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();value=collect(args.root,args.reference)
    with args.output.open('x') as stream:json.dump(value,stream,indent=2);stream.write('\n')
    print(json.dumps(dict(status='PASS',checkpoint=value['validation']['checkpoint'],
        formats=7,questions_per_format=864,output_sha256=sha(args.output))))
