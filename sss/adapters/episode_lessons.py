"""Export approved practice spans to PCC's opt-in lesson schema, without training."""
from sss.lesson_targets import target_segments
from sss.records import digest

def pcc_lesson(title,model_contract_id,segments,*,archive_sha256,verification_sha256,renderer_sha256,tokenizer_sha256,skill_id=None,target_policy='verified_thinking_actions_answer'):
    target_segments(segments,target_policy)
    if any(s.get('scope')!='practice' for s in segments):raise ValueError('Only approved practice can become a lesson')
    fields=('role','kind','rendered','verified','scope')
    lesson=dict(schema=2,title=title,model_contract_id=model_contract_id,segments=[{k:s[k] for k in fields} for s in segments],target_policy=target_policy,scope='owned-training',evidence=dict(method='sss-verified-episode-v1',archive_sha256=archive_sha256,verification_sha256=verification_sha256,renderer_sha256=renderer_sha256,tokenizer_sha256=tokenizer_sha256))
    if skill_id is not None:lesson['skill_id']=skill_id
    return lesson
