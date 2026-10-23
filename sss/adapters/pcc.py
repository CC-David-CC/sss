from pathlib import Path
import json
from sss.guard import SkillTree,SkillGuardRunner
from sss.records import digest
from .native_oracle import oracle_process

class DenseArithmeticEvaluator:
    """Fresh native expression generation; no evaluation answer becomes a lesson."""
    def __init__(self,tree,model,oracle,gpu_uuid,tokenizer):
        self.tree=tree;self.model=model;self.oracle=oracle;self.gpu=gpu_uuid;self.tokenizer=tokenizer
        from sss.suites.legacy_ceiling import check
        self.check=check
        from sss.records import file_sha256 as sha256
        self.contract_id=digest(dict(oracle_sha256=sha256(oracle),checker_sha256=sha256(Path(check.__code__.co_filename)),
                                     inference_harness_sha256=sha256(Path(oracle_process.__code__.co_filename)),maximum_new_tokens=24))
        for case in tree.cases.values():
            if (case['kind'] not in ('add','multiply','floor','ceil','abs')
                    or len(case['parameters'])!=(1 if case['kind']=='abs' else 2)):
                raise ValueError('This evaluator currently covers five arithmetic skills only')

    def __call__(self,candidate,split,path,worker_fd):
        from .native_oracle import oracle_process,completion
        path=Path(path);path.mkdir(mode=0o700,exist_ok=False)
        model=self.model;adapter=None
        if candidate:
            from sss.records import file_sha256 as sha256
            if sha256(candidate['candidate_path'])!=candidate['candidate_sha256']:raise ValueError('Evaluation candidate hash differs')
            if candidate['mode']=='full':model=candidate['candidate_path']
            else:adapter=candidate['candidate_path']
        records=[]
        with oracle_process(self.oracle,model,self.gpu,path/'oracle.log',adapter,extra_pass_fds=(worker_fd,)) as proc:
            for row in self.tree.rows(split):
                text=completion(proc,self.tokenizer,row['prompt']);verdict=self.check(row,text)
                records.append(dict(id=row['id'],passed=verdict['passed'],completion=text,verdict=verdict))
        (path/'observations-private.json').write_text(json.dumps(records,indent=2)+'\n')
        return records

def configured_guard(path,native,tokenizer):
    config=json.loads(Path(path).read_bytes())
    if set(config)!={'schema','tree','oracle','evaluation_gpu_uuid','round_examples','max_rounds','focus_fraction'} or config['schema']!=1:
        raise ValueError('Invalid owner skill-guard configuration')
    tree=SkillTree(json.loads(Path(config['tree']).read_bytes()))
    evaluate=DenseArithmeticEvaluator(tree,native.config['model'],config['oracle'],config['evaluation_gpu_uuid'],tokenizer)
    return SkillGuardRunner(native,tree,evaluate,round_examples=config['round_examples'],max_rounds=config['max_rounds'],focus_fraction=config['focus_fraction'])
