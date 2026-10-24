"""Versioned owned practice documents, without model/runtime authority."""
import copy
import re
from sss.records import digest

KINDS = {'actual_model_optimizer_mechanics_pilot':'pilot_id',
         'fixed_compute_optimizer_study_practice':'practice_id'}

def validate_training_document(document):
    if type(document) is not dict or type(document.get('schema')) is not int or document.get('schema') != 1:
        raise ValueError('Versioned owned training document required')
    key = KINDS.get(document.get('purpose')) if type(document.get('purpose')) is str else None
    if key is None or any(other in document for other in KINDS.values() if other != key):
        raise ValueError('Explicit supported practice identity kind required')
    identity = digest({k:v for k,v in document.items() if k != key})
    if document.get(key) != identity:
        raise ValueError('Checked practice document identity differs')
    if document.get('protected_cases_exported') is not False or document.get('target_policy') != 'actions_answer':
        raise ValueError('Unexpected practice split or target policy')
    if any(not re.fullmatch('[0-9a-f]{64}',str(document.get(k,''))) for k in ('model_sha256','model_contract_id')):
        raise ValueError('Pinned model and model-contract identities required')
    examples = document.get('examples');selection = document.get('selection')
    if type(examples) is not list or not examples or type(selection) is not list or len(selection) != len(examples):
        raise ValueError('Aligned admitted practice and selection required')
    if any(type(e) is not dict for e in examples + selection):
        raise ValueError('Training and selection rows must be objects')
    ids = [e.get('id') for e in examples]
    if any(type(i) is not str or not re.fullmatch('[A-Za-z0-9_-]{1,128}',i) for i in ids):
        raise ValueError('Bounded explicit lesson identifiers required')
    if len(set(ids)) != len(ids) or ids != [e.get('lesson_id') for e in selection] or any(e.get('verified') is not True for e in examples):
        raise ValueError('Practice examples differ from uniquely admitted lessons')
    return dict(data_id=identity,identity_field=key,kind=document['purpose'],
                model_sha256=document['model_sha256'],model_contract_id=document['model_contract_id'],
                examples=copy.deepcopy(examples),selection=copy.deepcopy(selection))


def validate_optimizer_program(program, document, arm_id):
    """Bind one predeclared optimizer arm to a complete interleaved practice set.

    This validates curriculum identity and order only. The PCC host still owns
    resource admission, native optimizer validation and candidate publication.
    """
    import math
    data = validate_training_document(document)
    if data['kind'] != 'fixed_compute_optimizer_study_practice':
        raise ValueError('Optimizer study requires its own practice document')
    if type(program) is not dict or type(program.get('schema')) is not int or program.get('schema') != 1 or program.get('kind') != 'sss.optimizer-learning-program.v1':
        raise ValueError('Versioned optimizer learning program required')
    identity = digest({k:v for k,v in program.items() if k != 'program_id'})
    if program.get('program_id') != identity:
        raise ValueError('Pinned optimizer program identity differs')
    for key,want in [('practice_id',data['data_id']),('pack_id',document.get('pack_id')),('model_sha256',data['model_sha256'])]:
        if program.get(key) != want:
            raise ValueError('Optimizer program differs from admitted practice: '+key)
    order = program.get('ordered_example_ids')
    by_id = {e['id']:e for e in data['examples']}
    if type(order) is not list or any(type(i) is not str for i in order) or len(order) != len(by_id) or len(set(order)) != len(order) or set(order) != set(by_id):
        raise ValueError('Program must order every admitted occurrence exactly once')
    if program.get('ordering') not in ('round-skill-gate-v1','round-review-repair-v1'):
        raise ValueError('Explicit interleaved curriculum order required')
    rows = {row['lesson_id']:row for row in data['selection']}
    if any(type(row.get('skill_id')) is not str or not row['skill_id'] or type(row.get('gate')) is not str for row in rows.values()):
        raise ValueError('Explicit skill and gate identifiers required')
    groups = {(row['skill_id'],row['gate']) for row in rows.values()}
    skills = {skill for skill,gate in groups}
    expected = {(skill,gate) for skill in skills for gate in ('independent','composition','transfer_recovery')}
    repair=program.get('repair_groups',[])
    if type(repair) is not list or any(type(row) is not dict or set(row)!={'skill_id','gate'} or type(row['skill_id']) is not str or type(row['gate']) is not str for row in repair):
        raise ValueError('Explicit repair skill/gate pairs required')
    repair_pairs=[(row['skill_id'],row['gate']) for row in repair]
    if len(set(repair_pairs))!=len(repair_pairs) or not set(repair_pairs)<=expected or (program['ordering']=='round-skill-gate-v1' and repair_pairs) or (program['ordering']=='round-review-repair-v1' and not repair_pairs):
        raise ValueError('Repair groups must be distinct covered gates in the explicit repair profile')
    batch = program.get('batch_size')
    if not skills or any(type(s) is not str or not s for s in skills) or groups != expected or type(batch) is not int or batch != len(expected)+len(repair_pairs) or len(order)%batch:
        raise ValueError('Every update must include every declared skill and mastery gate')
    expected_order = [(skill,gate) for skill in dict.fromkeys(row['skill_id'] for row in data['selection']) for gate in ('independent','composition','transfer_recovery')]+repair_pairs
    if any([(rows[i].get('skill_id'),rows[i].get('gate')) for i in order[start:start+batch]] != expected_order for start in range(0,len(order),batch)):
        raise ValueError('Declared round-skill-gate interleaving differs')
    seconds = program.get('training_budget_seconds'); cap = program.get('step_cap')
    if type(seconds) not in (int,float) or not math.isfinite(seconds) or not 0 < seconds < 3600 or type(cap) is not int or not 1 <= cap <= 1000:
        raise ValueError('Bounded training time and update cap required')
    arms = program.get('arms')
    if type(arms) is not list or not arms or any(type(a) is not dict or type(a.get('id')) is not str for a in arms) or len({a['id'] for a in arms}) != len(arms):
        raise ValueError('Uniquely named predeclared optimizer arms required')
    selected = [a for a in arms if a['id'] == arm_id]
    if len(selected) != 1:
        raise ValueError('Selected optimizer arm is not in the pinned program')
    arm = selected[0]; rate = arm.get('learning_rate')
    if arm.get('optimizer') not in ('adamw','muon') or type(rate) not in (int,float) or not math.isfinite(rate) or rate <= 0 or type(arm.get('settings')) is not dict:
        raise ValueError('Explicit optimizer, positive rate and settings required')
    return dict(program_id=identity,arm=copy.deepcopy(arm),batch_size=batch,steps=cap,
                training_budget_seconds=seconds,examples=[copy.deepcopy(by_id[i]) for i in order])


def make_review_repair_document(document, repair_groups, *, rounds):
    """Select checked practice: every gate once plus one extra per repair group.

    Inputs are already admitted practice. Evaluation answers and case IDs are
    neither accepted nor exported by this selector. Extra lessons are distinct
    occurrences from the checked pool, not forged duplicate lesson identities.
    """
    data=validate_training_document(document)
    if data['kind']!='fixed_compute_optimizer_study_practice' or type(rounds) is not int or not 1<=rounds<=128:
        raise ValueError('Bounded checked study practice required')
    if type(repair_groups) is not list or not repair_groups or any(type(row) is not dict or set(row)!={'skill_id','gate'} or type(row['skill_id']) is not str or type(row['gate']) is not str for row in repair_groups):
        raise ValueError('Repair proposals contain only skill/gate pairs')
    repair=[(row['skill_id'],row['gate']) for row in repair_groups]
    pools={}
    for row in data['selection']:
        key=(row.get('skill_id'),row.get('gate'));pools.setdefault(key,[]).append(row['lesson_id'])
    skills=list(dict.fromkeys(row['skill_id'] for row in data['selection']))
    review=[(skill,gate) for skill in skills for gate in ('independent','composition','transfer_recovery')]
    if set(pools)!=set(review) or len(set(repair))!=len(repair) or not set(repair)<=set(review):raise ValueError('Repair and review must cover admitted skill/gate families')
    if any(len(pools[key])<rounds*(2 if key in repair else 1) for key in review):raise ValueError('Insufficient distinct verified practice; no relabeling or automatic refill')
    order=[]
    for index in range(rounds):
        order.extend(pools[key][index*(2 if key in repair else 1)] for key in review)
        order.extend(pools[key][index*2+1] for key in repair)
    examples={e['id']:e for e in data['examples']};selection={e['lesson_id']:e for e in data['selection']}
    value=copy.deepcopy(document);value.pop('practice_id')
    value.update(origin='Owned independently checked practice selected using aggregate failure families; no protected answers',
                 source_practice_id=data['data_id'],source_document_id=digest(document),
                 block_policy=dict(ordering='round-review-repair-v1',repair_groups=copy.deepcopy(repair_groups),rounds=rounds,batch_size=len(review)+len(repair),review_groups=[dict(skill_id=s,gate=g) for s,g in review]),
                 examples=[examples[i] for i in order],selection=[selection[i] for i in order])
    value['practice_id']=digest(value);validate_training_document(value);return value


def working_parent_binding(parent, parent_document, document):
    """Explicit weight continuation with fresh moments for a changed block.

    The existing PCC executor still verifies the actual candidate's bytes and
    native architecture/resources. This does not grant paths to a remote client.
    """
    old=validate_training_document(parent_document);new=validate_training_document(document)
    if type(parent) is not dict or parent.get('result_id')!=digest({k:v for k,v in parent.items() if k!='result_id'}) or parent.get('status')!='MECHANICS_COMPLETE':
        raise ValueError('Completed pinned working-parent result required')
    if parent.get('data_id',parent.get(old['identity_field']))!=old['data_id'] or old['model_contract_id']!=new['model_contract_id'] or old['model_sha256']!=new['model_sha256']:
        raise ValueError('Working-parent source practice or original model family differs')
    candidate=parent.get('candidate',{})
    if candidate.get('mode')!='full' or type(candidate.get('candidate_path')) is not str or not candidate['candidate_path'] or not re.fullmatch('[0-9a-f]{64}',str(candidate.get('candidate_sha256',''))):
        raise ValueError('Registered standalone full-weight parent required')
    return dict(model=candidate['candidate_path'],base_sha256=candidate['candidate_sha256'],
                working_parent_result_id=parent['result_id'],previous_data_id=old['data_id'],next_data_id=new['data_id'],
                optimizer_state_transition='fresh_for_explicit_new_block')
