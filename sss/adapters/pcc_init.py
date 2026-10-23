import argparse,hashlib,json
from pathlib import Path
from sss.guard import SkillTree
from sss.records import digest
from sss.suites.arithmetic import KINDS,generated
from sss.suites.legacy_ceiling import check

def initialize(service,*,practice_per_skill=64,validation_per_skill=8,blind_per_skill=8):
    if not 16<=practice_per_skill<=2048 or not 2<=validation_per_skill<=128 or not 2<=blind_per_skill<=128:
        raise ValueError('Declare bounded practice and independent check coverage')
    def node(identity,title,parent,practice=(),validation=(),blind=()):
        return dict(id=identity,title=title,parent=parent,minimum_accuracy=.9,practice_lesson_ids=list(practice),validation=list(validation),blind=list(blind))
    nodes=[node('python','Python',None),node('python.arithmetic','Integer arithmetic','python')]
    provenance=service.root/'practice-evidence';provenance.mkdir(mode=0o700,exist_ok=True)
    for kind,(title,_) in KINDS.items():
        skill='python.arithmetic.'+kind;ids=[]
        for row,completion in generated(kind,'practice',practice_per_skill*4):
            negative=dict(source='constructed negative control, not observed model output',case=row,completion=' 0\n',verdict=check(row,' 0\n'))
            if negative['verdict']['passed']:raise ValueError('Constructed negative control unexpectedly passed')
            evidence=dict(method='host-verified-replay-v1',failed_result_sha256=digest(negative),
                corrected_result_sha256=digest(dict(prompt=row['prompt'],completion=completion)),
                verification_sha256=digest(dict(case=row,verdict=check(row,completion),purpose='owned retention practice; not a newly observed model failure')))
            lesson=dict(schema=1,title=title+' retention practice',model_contract_id=service.model,prompt=row['prompt'],completion=completion,
                rationale='Owned replay example checked by exact arithmetic; not a claim that this model failed this prompt.',
                scope='owned-training',skill_id=skill,evidence=evidence)
            prefix=service.tokenize(lesson['prompt']);full=service.tokenize(lesson['prompt']+lesson['completion'])
            if full[:len(prefix)]!=prefix or not 2<=len(full)-1<=service.max_tokens:continue
            service._write(provenance/(row['id']+'.json'),dict(negative=negative,positive=dict(case=row,completion=completion,verdict=check(row,completion))))
            accepted=service.submit('/cow/training/lessons',dict(operation_id='skill-practice-'+row['id'][:32],lesson=lesson));ids.append(accepted['lesson_id'])
            if len(ids)==practice_per_skill:break
        if len(ids)!=practice_per_skill:raise ValueError('Not enough practice fits token budget; no examples were truncated')
        validation=[r for r,_ in generated(kind,'validation',validation_per_skill)]
        blind=[r for r,_ in generated(kind,'blind',blind_per_skill)]
        nodes.append(node(skill,title,'python.arithmetic',ids,validation,blind))
    document=dict(schema=1,model_contract_id=service.model,nodes=nodes)
    SkillTree(document);return document

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--training-config',type=Path,required=True);parser.add_argument('--profile',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True);parser.add_argument('--practice-per-skill',type=int,default=64)
    parser.add_argument('--validation-per-skill',type=int,default=8);parser.add_argument('--blind-per-skill',type=int,default=8)
    args=parser.parse_args(argv)
    if args.output.exists():parser.error('Choose a new private tree path; existing evidence is not overwritten')
    config=json.loads(args.training_config.read_bytes());profile=json.loads(args.profile.read_bytes())
    if Path(config['runner']['model']).resolve()!=Path(profile['model_path']).resolve():parser.error('Profile must identify the training model tokenizer')
    from tools.strata_tokenizer import Tokenizer
    tokenizer=Tokenizer.from_gguf(config['runner']['model'])
    def no_training(*args):raise RuntimeError('Initialization has no training authority')
    from tools.pcc_lessons import LessonService
    service=LessonService(config['directory'],profile['model_contract_id'],tokenizer.encode,no_training,
                          max_tokens=config['max_tokens'],max_steps=config['max_steps'])
    try:
        tree=initialize(service,practice_per_skill=args.practice_per_skill,validation_per_skill=args.validation_per_skill,blind_per_skill=args.blind_per_skill)
        with args.output.open('x') as out:out.write(json.dumps(tree,indent=2)+'\n')
        args.output.chmod(0o600);print(json.dumps(SkillTree(tree).describe()))
    finally:service.close()

if __name__=='__main__':main()
