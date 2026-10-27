from pathlib import Path
import hashlib,json,re
r=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
scores={};evidence={}
for name,folder in [('original-F16','remix-original-f16-eu'),('trained-Q5','remix-trained-q5-eu')]:
    rows={}
    for kind,file in [('gsm8k','remix-gsm8k32-eu.json'),('arc','remix-arc32-eu.json')]:
        for item in read(r/file)['rows']:
            case=item['row'];key=f"{kind}:{item['row_idx']}"
            p=r/folder/(key.replace(':','-')+'.json');v=read(p)
            answer=v['response']['choices'][0]['message']['content']
            if kind=='gsm8k':
                m=re.search(r'####\s*([-+]?\d[\d,]*(?:\.\d+)?)',answer)
                expected=case['answer'].split('####')[-1].strip().replace(',','')
                correct=bool(m and m.group(1).replace(',','')==expected)
            else:correct=answer.strip()==case['answerKey']
            assert v['correct']==correct and key==v['case_id']
            rows[key]=dict(correct=correct,finished=v['response']['choices'][0]['finish_reason']=='stop')
            evidence[name+'/'+p.name]=sha(p)
    assert len(rows)==64;scores[name]=rows
a,b=scores.values()
summary=read(r/'remix-result-eu.json')
for row in summary['summaries']:
    assert row['correct']==sum(v['correct'] for v in scores[row['model']].values())
summary.update(answer_gains=sum(not a[k]['correct'] and b[k]['correct'] for k in a),
    answer_losses=sum(a[k]['correct'] and not b[k]['correct'] for k in a),
    naturally_finished={n:sum(v['finished'] for v in rows.values()) for n,rows in scores.items()},
    response_sha256=evidence,dataset_payload_sha256={n:sha(r/n) for n in ['remix-gsm8k32-eu.json','remix-arc32-eu.json']},
    source_sha256=sha(r/'run-remix-external-eu.py'),scope='First 32 GSM8K test and ARC-Challenge test rows; strict extraction; descriptive spot check, not official benchmark or training-only causal estimate')
(r/'remix-external-verified-eu.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k not in ['response_sha256']}))
