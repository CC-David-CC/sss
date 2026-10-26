"""Immutable teaching/evaluation archives, never an execution or permission ledger."""
from pathlib import Path
from collections import Counter
import hashlib
import json
import os
import re
from .records import canonical,digest
from .lesson_targets import target_segments

ROLES=('system','user','assistant','tool')
KINDS=('instruction','question','observation','thinking','action','answer','summary','framing')
SCOPES=('practice','development','qualification','private')

class EpisodeArchive:
    def __init__(self,path,*,create=False,metadata=None):
        self.path=Path(path).absolute()
        if create:
            self.path.mkdir(mode=0o700,parents=True,exist_ok=False)
            if type(metadata) is not dict or not metadata.get('origin'):raise ValueError('Archive needs explicit provenance')
            self._exclusive(self.path/'metadata.json',canonical(dict(schema=2,metadata=metadata))+b'\n')
            (self.path/'events').mkdir(mode=0o700)
        if self.path.is_symlink():raise ValueError('Archive must be an owned directory')
        self.metadata=json.loads((self.path/'metadata.json').read_bytes())
        if set(self.metadata)!={'schema','metadata'} or self.metadata['schema']!=2:raise ValueError('Unknown archive metadata')
        self._events=[];previous=digest(self.metadata)
        for index,path in enumerate(sorted((self.path/'events').iterdir())):
            if path.is_symlink() or path.name!=f'{index:08d}.json':raise ValueError('Unexpected or incomplete archive record')
            row=json.loads(path.read_bytes())
            self._validate(row,index,previous)
            self._events.append(row);previous=row['id']
        self.head=previous
    @staticmethod
    def _exclusive(path,raw):
        fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        with os.fdopen(fd,'wb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
        path.chmod(0o400)
    def _validate(self,row,index,previous):
        fields={'seq','previous','role','kind','text','verified','scope','refs','topic','question_id','resolves','id'}
        if type(row) is not dict or set(row)!=fields:raise ValueError('Invalid episode fields')
        if type(row['seq']) is not int or row['seq']!=index or row['previous']!=previous:raise ValueError('Broken archive order')
        if row['id']!=digest({k:v for k,v in row.items() if k!='id'}):raise ValueError('Changed episode evidence')
        if row['role'] not in ROLES or row['kind'] not in KINDS or row['scope'] not in SCOPES:raise ValueError('Unknown episode segment')
        if type(row['text']) is not str or len(row['text'].encode())>4*1024*1024:raise ValueError('Invalid episode text')
        if type(row['verified']) is not bool:raise ValueError('Explicit verification flag required')
        if row['kind']=='framing' and (row['role']!='assistant' or row['verified'] is not False):raise ValueError('Framing must be unverified assistant template bytes')
        if any(type(row[k]) is not str for k in ('topic','question_id','resolves')):raise ValueError('Invalid topic/question identity')
        if type(row['refs']) is not list or any(type(v) is not str for v in row['refs']):raise ValueError('Invalid source references')
        visible={e['id'] for e in self._events}
        if any(ref not in visible for ref in row['refs']):raise ValueError('Reference is absent or from the future')
        if row['question_id'] and any(e['question_id']==row['question_id'] for e in self._events):raise ValueError('Duplicate question identity')
        if row['resolves'] and (row['verified'] is not True or row['kind']!='answer' or row['resolves'] not in {e['question_id'] for e in self._events}):raise ValueError('Resolution needs a verified answer to an existing question')
    def append(self,role,kind,text,*,verified=False,scope='practice',refs=(),topic='',question_id='',resolves=''):
        row=dict(seq=len(self._events),previous=self.head,role=role,kind=kind,text=text,verified=verified,scope=scope,refs=list(refs),topic=topic,question_id=question_id,resolves=resolves)
        row['id']=digest(row);self._validate(row,row['seq'],self.head)
        self._exclusive(self.path/'events'/f"{row['seq']:08d}.json",canonical(row)+b'\n')
        self._events.append(row);self.head=row['id'];return row['id']
    def records(self,through=None):
        if through is None:through=len(self._events)-1
        if type(through) is not int or not -1<=through<len(self._events):raise ValueError('Invalid visibility boundary')
        return json.loads(json.dumps(self._events[:through+1]))
    def read(self,identity,*,through=None):
        matches=[row for row in self.records(through) if row['id']==identity]
        if len(matches)!=1:raise ValueError('Record not visible')
        return matches[0]
    def search(self,query,*,through=None,limit=8):
        if type(query) is not str or len(query)>8192 or type(limit) is not int or not 1<=limit<=64:raise ValueError('Bounded archive query required')
        terms=set(re.findall(r'\w+',query.casefold()));results=[]
        for row in self.records(through):
            counts=Counter(re.findall(r'\w+',(row['topic']+' '+row['text']).casefold()))
            score=sum(min(counts[t],3) for t in terms)
            if score:results.append(dict(id=row['id'],seq=row['seq'],topic=row['topic'],score=score,snippet=row['text'][:512]))
        return sorted(results,key=lambda r:(-r['score'],-r['seq']))[:limit]

def compact_reference(archive,through,*,count,budget,unit):
    """Causal extractive teaching baseline. No future query is an input."""
    if type(budget) is not int or budget<128 or not unit:raise ValueError('Explicit summary budget/unit required')
    rows=archive.records(through)
    if not rows:raise ValueError('Cannot summarize an empty archive')
    answered={r['resolves'] for r in rows if r['resolves']}
    pending=[r for r in rows if r['question_id'] and r['question_id'] not in answered]
    note=dict(schema=2,as_of=through,source_head=rows[-1]['id'],unit=unit,budget=budget,
        open_question_count=len(pending),archive_index_through=through,entries=[])
    # Prioritize unresolved questions, then last verified observation per topic.
    latest={}
    for row in rows:
        if row['verified'] and row['kind'] in ('observation','answer'):latest[row['topic']]=row
    choices=list(reversed(pending))+list(reversed(list(latest.values())))
    seen=set()
    for row in choices:
        if row['id'] in seen:continue
        seen.add(row['id']);entry=dict(record_id=row['id'],topic=row['topic'],quote=row['text'][:1024],question_id=row['question_id'])
        proposal=dict(note,entries=note['entries']+[entry])
        if count(canonical(dict(proposal,note_id='0'*64)).decode())<=budget:note=proposal
    if count(canonical(dict(note,note_id='0'*64)).decode())>budget:raise ValueError('Summary metadata does not fit the budget')
    note['note_id']=digest(note)
    return note

def verify_note(archive,note):
    if type(note) is not dict or note.get('note_id')!=digest({k:v for k,v in note.items() if k!='note_id'}):raise ValueError('Changed compaction note')
    rows=archive.records(note['as_of'])
    if not rows or rows[-1]['id']!=note['source_head'] or note['archive_index_through']!=note['as_of']:raise ValueError('Wrong compaction source')
    answered={r['resolves'] for r in rows if r['resolves']}
    if note['open_question_count']!=sum(bool(r['question_id']) and r['question_id'] not in answered for r in rows):raise ValueError('Lost unresolved question count')
    for entry in note['entries']:
        row=archive.read(entry['record_id'],through=note['as_of'])
        if entry['topic']!=row['topic'] or entry['question_id']!=row['question_id'] or entry['quote']!=row['text'][:1024]:raise ValueError('Unsupported summary claim')
    return True

def training_tokens(segments,*,tokenize,policy='verified_thinking_actions_answer',maximum=8192):
    """Tokenize already-rendered, exact template spans with aligned role boundaries.

The caller supplies the model's renderer/tokenizer. This is not a generic chat
renderer. Masking targets does not detach earlier activations from backprop.
"""
    selected=target_segments(segments,policy);raw='';tokens=[];labels=[]
    for segment,train in zip(segments,selected):
        if segment.get('scope')!='practice':raise ValueError('Only approved practice may become training targets/context')
        text=segment.get('rendered')
        if type(text) is not str:raise ValueError('Exact rendered spans required')
        raw+=text;next_tokens=tokenize(raw)
        if type(next_tokens) is not list or any(type(t) is not int or t<0 for t in next_tokens):raise ValueError('Invalid tokenizer output')
        if next_tokens[:len(tokens)]!=tokens:raise ValueError('Template segment boundary does not align with tokenizer')
        labels.extend([train]*(len(next_tokens)-len(tokens)));tokens=next_tokens
    if not 2<=len(tokens)-1<=maximum:raise ValueError('Export exceeds admitted length; nothing was truncated')
    if not any(labels[1:]):raise ValueError('No predictable target tokens')
    return dict(tokens=tokens[:-1],targets=tokens[1:],loss_mask=labels[1:],target_policy=policy,
                text_sha256=hashlib.sha256(raw.encode()).hexdigest(),weights_updated=False)

def render_text(archive,*,public=False):
    """The existing completed-record bytes, without writing or another authority."""
    rows=archive.records()
    if public and (archive.metadata['metadata'].get('origin')!='synthetic' or any(r['scope']!='practice' for r in rows)):
        raise ValueError('Public examples must be owned synthetic practice')
    if not any(r['kind']=='answer' and r['verified'] for r in rows):raise ValueError('No verified completed answer')
    text=['Skills cubed: completed teaching record','Artifact complete; no model weight update is implied.','Archive head: '+archive.head,'']
    for row in rows:
        text += [f"[{row['seq']} | {row['role']} | {row['kind']} | verified={row['verified']} | id={row['id']}]",row['text'],'']
    return '\n'.join(text).encode()

def export_text(archive,path,*,public=False):
    raw=render_text(archive,public=public)
    EpisodeArchive._exclusive(Path(path),raw)
    rows=archive.records()
    return dict(archive_head=archive.head,sha256=hashlib.sha256(Path(path).read_bytes()).hexdigest(),records=len(rows),trained=False)
