"""Causal long archive mechanics on owned computing-lab experiments.

Reference byte tokens match the tiny CPU fixture vocabulary. This is explicitly
not a Wen tokenizer or a million-token live context claim.
"""
from pathlib import Path
import argparse,json
from sss.episodes import EpisodeArchive,compact_reference,verify_note,export_text
from sss.research import experiment,finding,check_finding
from sss.records import canonical,digest

def rendered_size(row):return len(('<'+row['role']+'>\n'+row['text']+'\n</'+row['role']+'>\n').encode())

def build(root,minimum_tokens=1048576):
    if type(minimum_tokens) is not int or not 4096<=minimum_tokens<=8*1048576:raise ValueError('Bounded cumulative archive target required')
    root=Path(root);archive=EpisodeArchive(root,create=True,metadata=dict(origin='synthetic',story='computing-lab',tokenizer='reference-utf8-byte-v1',training=False))
    question=archive.append('user','question','Does indexing always save work, including the setup cost? Keep the first experiment record for a later revisit.',topic='research.search',question_id='opening')
    initial=experiment(907,48,1);early=archive.append('tool','observation',json.dumps(initial,sort_keys=True),verified=True,topic='initial-measurement',refs=[question])
    archived_tokens=sum(rendered_size(row) for row in archive.records());notes=[];measurements=[];index=0;last_note_tokens=0
    while archived_tokens<minimum_tokens:
        day=index//4;topic=('math','logic','code','linux')[index%4]
        q=archive.append('user','question',f'Day {day}, {topic} class. Investigate size {32+(index%16)*16}, query count {1+(index%31)*2}, seed {10000+index}. Predict whether indexing pays for its setup, then measure it.',topic=topic,question_id='round-'+str(index))
        row=experiment(10000+index,32+(index%16)*16,1+(index%31)*2);measurements.append(row)
        obs=archive.append('tool','observation',json.dumps(row,sort_keys=True),verified=True,topic=topic,refs=[q])
        conclusion=finding([row]);answer=json.dumps(conclusion,sort_keys=True)
        if not check_finding([row],answer):raise AssertionError('Independent research check failed')
        archive.append('assistant','answer',answer,verified=True,topic=topic,refs=[q,obs],resolves='round-'+str(index))
        archived_tokens+=sum(rendered_size(r) for r in archive.records()[-3:]);index+=1
        if archived_tokens-last_note_tokens>=98304:
            note=compact_reference(archive,len(archive.records())-1,count=lambda text:len(text.encode()),budget=32768,unit='reference-utf8-byte-tokens')
            verify_note(archive,note);notes.append(note);last_note_tokens=archived_tokens
    # The old detail is deliberately not in the final working note. The late
    # question was not supplied to any compactor; answering needs the archive.
    note=compact_reference(archive,len(archive.records())-1,count=lambda t:len(t.encode()),budget=2048,unit='reference-utf8-byte-tokens')
    note['entries']=[e for e in note['entries'] if e['record_id']!=early]
    note['note_id']=digest({k:v for k,v in note.items() if k!='note_id'});verify_note(archive,note);notes.append(note)
    late=archive.append('user','question','Revisit our original measurement with seed 907. What was its input identity and the complete indexing cost? Reread the archived record; the current note omits those values.',topic='research.search',question_id='late-revisit')
    matches=archive.search('907 initial-measurement',limit=64)
    if early not in {r['id'] for r in matches}:raise AssertionError('Old experiment is not retrievable')
    source=archive.read(early);restored=json.loads(source['text'])
    answer=json.dumps(dict(input_sha256=restored['input_sha256'],indexed_total=restored['indexed_total'],source_record=early))
    archive.append('assistant','answer',answer,verified=restored==experiment(907,48,1),topic='research.search',refs=[late,early],resolves='late-revisit')
    archive.append('assistant','answer',json.dumps(finding([initial,*measurements]),sort_keys=True),verified=True,topic='research.search',refs=[question,early],resolves='opening')
    # Reopen checks every immutable source record and its chain.
    reopened=EpisodeArchive(root);assert reopened.head==archive.head
    (root/'compactions.json').write_text(json.dumps(notes,indent=2)+'\n')
    txt=export_text(archive,root/'conversation.txt',public=True)
    result=dict(schema=1,status='PASS',scope='reference archive, compaction and retrieval mechanics',cumulative_tokens=archived_tokens,tokenizer='reference-utf8-byte-v1',meaningful_experiments=len(measurements)+1,compactions=len(notes),late_source_record=early,source_omitted_from_last_note=True,omission='controlled withheld detail for archive-retrieval testing',archive_head=archive.head,txt=txt,model_inference=False,weights_updated=False)
    (root/'result.json').write_text(json.dumps(result,indent=2)+'\n');return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--minimum-tokens',type=int,default=1048576);a=p.parse_args();print(json.dumps(build(a.output,a.minimum_tokens),indent=2))
