"""Freeze checked practice for a native optimizer mechanics pilot.

S3 owns the exercise split and verification. The caller owns PCC admission,
rendering, resources and execution. No model run or promotion happens here.
"""
from pathlib import Path
from dataclasses import asdict
from sss.adapters.foundation_training import build_pack,initialize,validate_pack
from sss.foundations import check,reference
from sss.records import canonical,digest

DEFAULT_COORDINATES=(('math.add.carry','independent',0),('math.subtract.borrow','composition',0),('math.place_value','transfer_recovery',0))

def prepare(service,renderer,output,*,tokenizer_sha256,model_sha256,coordinates=DEFAULT_COORDINATES):
 output=Path(output);output.mkdir(mode=0o700,parents=True,exist_ok=False)
 pack=build_pack(['math.add.carry','math.subtract.borrow'],seed=0,practice_per_gate=2,checks_per_gate=1)
 exercises=validate_pack(pack)
 tree=initialize(service,pack,renderer,renderer_sha256=renderer.renderer_sha256,tokenizer_sha256=tokenizer_sha256,target_policy='actions_answer')
 practice=[e for e in exercises if e.split=='practice'];protected=[e for e in exercises if e.split!='practice']
 records=[service.lesson(row['lesson_id']) for row in service.lessons()['lessons']]
 selected=[];evidence=[]
 for skill,gate,ordinal in coordinates:
  choices=[e for e in practice if e.skill_id==skill and e.gate==gate]
  if type(ordinal) is not int or not 0<=ordinal<len(choices):raise ValueError('Explicit implemented practice coordinate required')
  exercise=choices[ordinal];answer=reference(exercise)
  if not check(exercise,answer):raise ValueError('Practice answer failed its independent checker')
  verification=digest(dict(exercise_id=exercise.identity,checker_id=pack['implementation_id'],answer=answer,passed=True))
  matches=[row for row in records if row['lesson']['evidence']['verification_sha256']==verification]
  if len(matches)!=1:raise ValueError('Practice exercise is not uniquely bound to an admitted lesson')
  record=matches[0];example=record['example']
  if record['lesson']['target_policy']!='actions_answer' or example['verified'] is not True:raise ValueError('Unexpected practice target policy')
  text=''.join(s['rendered'] for s in record['lesson']['segments'])
  if any(e.prompt in text for e in protected):raise ValueError('Protected question reached the training selection')
  if example['id'] in {e['id'] for e in selected}:raise ValueError('Duplicate selected lesson')
  selected.append(example)
  evidence.append(dict(skill_id=skill,gate=gate,ordinal=ordinal,exercise_id=exercise.identity,lesson_id=record['lesson_id'],selected_targets=sum(example['loss_mask']),consumed_tokens=len(example['tokens']),verification_sha256=verification))
 result=dict(schema=1,purpose='actual_model_optimizer_mechanics_pilot',origin='owned synthetic practice, not observed model failures',model_contract_id=service.model,model_sha256=model_sha256,pack_id=pack['pack_id'],tree_id=tree.identity,renderer_sha256=renderer.renderer_sha256,tokenizer_sha256=tokenizer_sha256,target_policy='actions_answer',selection=evidence,examples=selected,protected_cases_exported=False,practice_lessons_admitted=len(practice),protected_check_count=len(protected),weights_updated=False,promoted=False)
 result['pilot_id']=digest(result)
 for name,value in [('selection-private.json',result),('pack-private.json',pack)]:
  with (output/name).open('xb') as stream:stream.write(canonical(value)+b'\n')
 with (output/'finished-training-examples.txt').open('x',encoding='utf-8') as stream:
  stream.write('OWNED SYNTHETIC PRACTICE; checked demonstrations, not model success or evaluation answers.\n')
  for row in evidence:
   exercise=next(e for e in practice if e.identity==row['exercise_id'])
   stream.write('\nSkill: '+row['skill_id']+'\nGate: '+row['gate']+'\nQuestion:\n'+exercise.prompt+'\nChecked answer:\n'+reference(exercise)+'\n')
 return result
