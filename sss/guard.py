"""A frozen skill tree, interleaved practice and bounded native repair rounds.

This is a training controller, not an inference/workflow ledger. Model outputs
cannot grant training authority. Checks guide practice selection, never labels.
"""
from pathlib import Path
from collections import Counter, defaultdict
import copy
import hashlib
import json
import math
import re
from .records import digest

SKILL=re.compile(r'[a-z][a-z0-9_.-]{0,95}\Z')

class SkillTree:
    def __init__(self,document):
        self.document=copy.deepcopy(document)
        document=self.document  # Detach caller-owned nested lists and dictionaries.
        if (set(document)!={'schema','model_contract_id','nodes'} or type(document['schema']) is not int or document['schema']!=1
                or not re.fullmatch('[a-f0-9]{64}',str(document['model_contract_id']))):
            raise ValueError('Skill tree schema 1 requires a model contract and explicit nodes')
        rows=document['nodes']
        if type(rows) is not list or not 1<=len(rows)<=128:raise ValueError('Use 1-128 skill nodes')
        self.nodes={};self.children=defaultdict(list);self.cases={};self.case_skill={}
        fields={'id','title','parent','minimum_accuracy','practice_lesson_ids','validation','blind'}
        for row in rows:
            if set(row)!=fields or not SKILL.fullmatch(row['id']) or row['id'] in self.nodes:
                raise ValueError('Unique bounded skill identifiers and exact node fields required')
            if type(row['title']) is not str or not 1<=len(row['title'])<=160:raise ValueError('Skill title required')
            threshold=row['minimum_accuracy']
            if type(threshold) not in (int,float) or not math.isfinite(threshold) or not .5<=threshold<=1:
                raise ValueError('Declare a finite accuracy requirement between 0.5 and 1')
            ids=row['practice_lesson_ids']
            if type(ids) is not list or len(set(ids))!=len(ids) or any(not re.fullmatch('[a-f0-9]{64}',v) for v in ids):
                raise ValueError('Practice must reference distinct owned lesson identities')
            self.nodes[row['id']]=row;self.children[row['parent']].append(row['id'])
        roots=self.children[None]
        if len(roots)!=1:raise ValueError('Declare one skill-tree root')
        for identity,row in self.nodes.items():
            seen={identity};parent=row['parent']
            while parent is not None:
                if parent not in self.nodes or parent in seen:raise ValueError('Missing parent or cycle in skill tree')
                seen.add(parent);parent=self.nodes[parent]['parent']
        self.leaves={k:v for k,v in self.nodes.items() if not self.children[k]}
        prompts=set();practice=set()
        for identity,row in self.nodes.items():
            if identity not in self.leaves:
                if row['practice_lesson_ids'] or row['validation'] or row['blind']:raise ValueError('Group nodes aggregate children; put examples on leaves')
                continue
            if not row['practice_lesson_ids'] or not row['validation'] or not row['blind']:
                raise ValueError('Every leaf needs practice, validation and blind coverage; unknown is not passing')
            if practice.intersection(row['practice_lesson_ids']):raise ValueError('One practice lesson cannot silently represent multiple skills')
            practice.update(row['practice_lesson_ids'])
            for split in ('validation','blind'):
                if type(row[split]) is not list:raise ValueError('Explicit case list required')
                for case in row[split]:
                    legacy={'id','prompt','kind','parameters'};generic={'id','prompt','checker'}
                    if set(case) not in (legacy,generic):raise ValueError('Evaluation cases contain checker contracts, not teaching completions')
                    if set(case)==generic:
                        checker=case['checker']
                        if (type(checker) is not dict or set(checker)!={'name','version','case_id'}
                                or type(checker['version']) is not int or checker['version']<1
                                or any(type(checker[k]) is not str or not 1<=len(checker[k])<=128 for k in ('name','case_id'))):
                            raise ValueError('A versioned registered checker contract is required')
                    else:
                        parameters=case['parameters']
                        if (type(parameters) is not list or not parameters or len(set(parameters))!=len(parameters)
                                or any(type(p) is not str or not p.isidentifier() for p in parameters)):
                            raise ValueError('Arithmetic evaluation requires distinct named parameters')
                    if (type(case['prompt']) is not str or not case['prompt'] or len(case['prompt'].encode())>65536
                            or case['id']!=hashlib.sha256(case['prompt'].encode()).hexdigest()
                            or case['id'] in self.cases or case['prompt'] in prompts):
                        raise ValueError('Evaluation identities must be unique exact prompt hashes')
                    self.cases[case['id']]=dict(case,split=split);self.case_skill[case['id']]=identity;prompts.add(case['prompt'])
        if len(self.cases)>2048:raise ValueError('Skill evaluation budget exceeds 2048 frozen cases')
        self.identity=digest(self.document)
        self._frozen_index=digest(self._index_document())

    def _index_document(self):
        return dict(nodes=self.nodes, cases=self.cases, case_skill=self.case_skill,
                    leaves=self.leaves, children=list(self.children.items()))

    def assert_frozen(self):
        if (digest(self.document)!=self.identity
                or digest(self._index_document())!=self._frozen_index):
            raise ValueError('Skill tree changed after freezing')

    def describe(self):
        self.assert_frozen()
        return dict(schema=1,tree_id=self.identity,model_contract_id=self.document['model_contract_id'],nodes=[
            dict(id=k,title=v['title'],parent=v['parent'],minimum_accuracy=v['minimum_accuracy'],
                 practice_examples=len(v['practice_lesson_ids']),validation_cases=len(v['validation']),blind_cases=len(v['blind']),
                 status='not_evaluated') for k,v in self.nodes.items()])

    def rows(self,split):
        self.assert_frozen()
        if split not in ('validation','blind'):raise ValueError('Unknown evaluation split')
        return copy.deepcopy([v for v in self.cases.values() if v['split']==split])

    def assess(self,records,split,protected=()):
        expected={v['id'] for v in self.rows(split)};by_id={v['id']:v for v in records}
        if len(records)!=len(by_id) or set(by_id)!=expected or any(type(v.get('passed')) is not bool for v in records):
            raise ValueError('Every frozen skill check needs exactly one boolean result; missing/unknown is not passing')
        passed={k for k,v in by_id.items() if v['passed']};lost=set(protected)-passed
        if not set(protected)<=expected:raise ValueError('Protected checks belong to another frozen suite')
        scores={};weak=[]
        for identity,node in self.leaves.items():
            ids={v['id'] for v in node[split]};hits=len(ids&passed)
            good=hits/len(ids)>=node['minimum_accuracy']
            scores[identity]=dict(passed=hits,total=len(ids),meets_requirement=good,
                                  regressions=len(ids&lost))
            if not good:weak.append(identity)
        return dict(scores=scores,passed_ids=sorted(passed),regressed_ids=sorted(lost),
                    regressed_skills=sorted({self.case_skill[k] for k in lost}),weak_skills=sorted(weak),
                    qualified=not weak and not lost)


class SkillGuardRunner:
    """Wrap the existing native runner; use its same parent/receipt/lease path."""
    def __init__(self,native,tree,evaluate,*,round_examples=32,max_rounds=4,focus_fraction=.5):
        if type(round_examples) is not int or not 2*len(tree.leaves)<=round_examples<=4096:
            raise ValueError('Round size must cover focused practice and every skill')
        if type(max_rounds) is not int or not 1<=max_rounds<=32:raise ValueError('Use a bounded 1-32 repair rounds')
        if type(focus_fraction) not in (int,float) or not math.isfinite(focus_fraction) or not .25<=focus_fraction<=.75:
            raise ValueError('Focus fraction must retain a substantial replay share')
        self.native=native;self.tree=tree;self.evaluate=evaluate;self.round_examples=round_examples
        self.max_rounds=max_rounds;self.focus_fraction=focus_fraction
        tree.assert_frozen()
        self.policy_id=digest(self._policy_document())

    def _policy_document(self):
        return dict(guard_revision=2, tree_id=self.tree.identity,
                    round_examples=self.round_examples, max_rounds=self.max_rounds,
                    focus_fraction=self.focus_fraction,
                    evaluator_contract=getattr(self.evaluate,'contract_id','controlled-test-callback'))

    def assert_frozen(self):
        self.tree.assert_frozen()
        if digest(self._policy_document())!=self.policy_id:
            raise ValueError('Skill guard policy changed after freezing')

    def _evaluate(self,candidate,split,path,worker_fd,protected=()):
        self.assert_frozen()
        records=self.evaluate(candidate,split,path,worker_fd)
        self.assert_frozen()
        return self.tree.assess(records,split,protected)

    def bind(self,read_lesson,make_example,tokenize,model):
        self.assert_frozen()
        if model!=self.tree.document['model_contract_id']:raise ValueError('Skill tree belongs to another model')
        self.read_lesson=read_lesson;self.make_example=make_example;self.tokenize=tokenize

    def describe_skills(self):
        self.assert_frozen()
        return dict(self.tree.describe(),policy_id=self.policy_id,
        round_examples=self.round_examples,max_rounds=self.max_rounds,focus_fraction=self.focus_fraction)

    def validate_request(self,request):
        self.assert_frozen()
        guard=request['skill_guard']
        if type(guard) is not dict or guard!={'policy_id':self.policy_id}:raise ValueError('Skill policy differs; inspect current skills before a new operation')
        per_round=math.ceil(self.round_examples/request['batch_size'])
        if request['steps']<per_round:raise ValueError('Step budget cannot cover one mixed skill round')
        if len(request['lesson_ids'])>int(self.round_examples*self.focus_fraction):raise ValueError('New lessons exceed focused share; select a smaller group')
        for identity in request['lesson_ids']:
            if self.read_lesson(identity)['lesson'].get('skill_id') not in self.tree.leaves:
                raise ValueError('Tag each new lesson with a registered leaf skill_id')

    def _materialize(self,request):
        self.assert_frozen()
        lessons={};pools={}
        check_tokens={}
        for case in self.tree.cases.values():
            tokens=tuple(self.tokenize(case['prompt']))
            if not tokens:raise ValueError('Protected prompt tokenization is empty')
            check_tokens.setdefault(len(tokens),set()).add(tokens)
        for skill,node in self.tree.leaves.items():
            pools[skill]=list(node['practice_lesson_ids'])
            for identity in pools[skill]:
                lesson=copy.deepcopy(self.read_lesson(identity)['lesson'])
                if lesson.get('skill_id')!=skill:raise ValueError('Practice lesson has the wrong skill tag')
                lessons[identity]=lesson
        for identity in request['lesson_ids']:
            lesson=copy.deepcopy(self.read_lesson(identity)['lesson']);lessons[identity]=lesson
            skill=lesson['skill_id']
            if identity not in pools[skill]:pools[skill].insert(0,identity)
        for identity,lesson in lessons.items():
            # Inspect admitted consumed tokens, including multi-turn schema-2
            # context. A protected prompt cannot hide behind a role prefix.
            example=self.make_example(lesson,identity)
            tokens=tuple(example['tokens'])+(example['targets'][-1],)
            if any(tokens[start:start+size] in protected
                   for size,protected in check_tokens.items()
                   for start in range(len(tokens)-size+1)):
                raise ValueError('Evaluation prompt/token material cannot enter training')
        self.assert_frozen()
        return lessons,pools

    def _select(self,pools,focus,cursors,required):
        # Round-robin within skill pools; evaluations only choose skill IDs.
        focus=sorted(set(focus));other=sorted(set(pools)-set(focus));picked=[];used=set()
        def add(skill):
            pool=pools[skill]
            for _ in range(len(pool)):
                identity=pool[cursors[skill]%len(pool)];cursors[skill]+=1
                if identity not in used:used.add(identity);picked.append(identity);return
            raise ValueError('Not enough distinct practice lessons for this mixed round')
        # Every requested lesson is actually consumed, and every skill appears.
        for identity in required:
            if identity not in used:used.add(identity);picked.append(identity)
        for skill in sorted(pools):
            if not any(v in used for v in pools[skill]):add(skill)
        target=int(self.round_examples*self.focus_fraction)
        while len(picked)<self.round_examples:
            focused=sum(any(v in pools[k] for k in focus) for v in picked)
            bucket=focus if focused<target or not other else other
            skill=bucket[(len(picked)-len(required))%len(bucket)];add(skill)
        # Shuffle neither away interleaving nor into skill blocks: cycle skills.
        grouped={k:[v for v in picked if v in pools[k]] for k in sorted(pools)};ordered=[]
        while any(grouped.values()):
            for values in grouped.values():
                if values:ordered.append(values.pop(0))
        return ordered

    def __call__(self,request,examples,run,parent,worker_fd):
        if 'skill_guard' not in request:return self.native(request,examples,run,parent,worker_fd)
        request=copy.deepcopy(request)
        self.validate_request(request)
        if parent and (parent.get('skill_guard',{}).get('qualified') is not True
                       or parent['skill_guard'].get('policy_id')!=self.policy_id):
            raise ValueError('Continue only a qualified hat under the same frozen skill policy')
        lessons,pools=self._materialize(request);run=Path(run);run.mkdir(mode=0o700,parents=True,exist_ok=False)
        self._write(run/'policy.json',dict(policy_id=self.policy_id,tree=self.tree.document,request=request))
        baseline=self._evaluate(parent,'validation',run/'baseline',worker_fd)
        protected=set(baseline['passed_ids'])
        if parent and not set(parent['skill_guard']['protected_pass_ids'])<=protected:raise ValueError('Parent no longer passes its protected skill checks')
        rounds=[];cursors=Counter();focus=sorted(set(baseline['weak_skills'])|{lessons[v]['skill_id'] for v in request['lesson_ids']})
        current=parent;candidate=None;last=baseline;per_round=math.ceil(self.round_examples/request['batch_size'])
        budget=min(self.max_rounds,request['steps']//per_round)
        def progress(stage,**extra):
            self._write(run/'progress.json',dict(tree_id=self.tree.identity,policy_id=self.policy_id,stage=stage,
                baseline=baseline['scores'],rounds=rounds,promoted=False,**extra))
        progress('baseline_checked')
        for index in range(budget):
            self.assert_frozen()
            selected=self._select(pools,focus,cursors,request['lesson_ids'] if index==0 else [])
            native_request=dict(request,lesson_ids=selected,steps=per_round);native_request.pop('skill_guard')
            self._write(run/('round-'+str(index)+'-selection.json'),dict(focus_skills=focus,lesson_ids=selected))
            progress('training',next_round=index+1,focus_skills=focus)
            candidate=self.native(native_request,[self.make_example(lessons[v],v) for v in selected],run/('round-'+str(index)),current,worker_fd)
            self.assert_frozen()
            progress('evaluating',next_round=index+1)
            last=self._evaluate(candidate,'validation',run/('check-'+str(index)),worker_fd,protected)
            row=dict(round=index+1,focus_skills=focus,examples=len(selected),distribution=dict(Counter(lessons[v]['skill_id'] for v in selected)),
                     candidate_sha256=candidate['candidate_sha256'],scores=last['scores'],regressed_skills=last['regressed_skills'],weak_skills=last['weak_skills'])
            rounds.append(row);progress('checkpoint_checked')
            if not last['regressed_ids']:protected.update(last['passed_ids'])
            current=candidate
            if last['qualified']:break
            focus=sorted(set(last['regressed_skills'])|set(last['weak_skills']))
        qualified=last['qualified'];blind=None;state='round_budget_exhausted'
        if qualified:
            original=self._evaluate(parent,'blind',run/'blind-original',worker_fd)
            blind=self._evaluate(candidate,'blind',run/'blind-candidate',worker_fd,original['passed_ids'])
            qualified=blind['qualified'];state='qualified' if qualified else 'blind_failed'
        report=dict(schema=1,tree_id=self.tree.identity,policy_id=self.policy_id,qualified=qualified,state=state,promoted=False,
                    baseline=baseline['scores'],rounds=rounds,final_scores=last['scores'],blind_scores=blind['scores'] if blind else None,
                    protected_pass_ids=sorted(protected),max_training_steps=request['steps'],training_steps=len(rounds)*per_round,
                    total_examples=len(rounds)*self.round_examples)
        self._write(run/'skill-report.json',report)
        return dict(candidate,skill_guard=report)

    @staticmethod
    def _write(path,value):
        temporary=path.with_suffix('.tmp');temporary.write_text(json.dumps(value,indent=2)+'\n');temporary.replace(path)
