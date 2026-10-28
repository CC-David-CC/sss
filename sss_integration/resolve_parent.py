"""Resolve a recomputed S3 proposal through PCC's owner-side artifact reader.

This writes a private continuation description. It never trains or promotes.
"""
from pathlib import Path
import argparse, hashlib, importlib, inspect, json, os, sys
from sss.learning import next_skill_block
from sss.records import digest


def resolve_proposal(pcc_root,proposal_file,baseline_file,parent_file,candidate_file,
                     version_file,profile_file,*,artifact_roots,state_policy,
                     base_model=None,checkpoint_file=None,examples_file=None):
    root=Path(pcc_root).resolve(strict=True)
    paths=[Path(p).resolve(strict=True) for p in (proposal_file,baseline_file,parent_file,candidate_file)]
    original=[p.read_bytes() for p in paths]
    proposal,baseline,parent,candidate=[json.loads(raw) for raw in original]
    expected=next_skill_block(baseline,parent,candidate)
    if proposal!=expected:raise ValueError('Proposal differs from its original frozen evaluations; recompute and review it')
    sys.path[:0]=[str(root),str(root/'experimental/branching_context/src')]
    module=importlib.import_module('tools.pcc_candidate_parent')
    if Path(module.__file__).resolve()!=root/'tools/pcc_candidate_parent.py':
        raise ValueError('Cached PCC resolver belongs to another checkout; use a fresh process')
    sources={}
    for value in [module.resolve_parent,module.read_optimizer_state,module.bind_dense_profile,module.GGUFFile]:
        source=Path(inspect.getsourcefile(value)).resolve(strict=True)
        if not source.is_relative_to(root):raise ValueError('PCC helper imported a different source checkout')
        sources[str(source.relative_to(root))]=source
    for name in ('llama_dense_backend','qwen35_lora'):
        relative='experimental/branching_context/src/context_time_travel/'+name+'.py'
        sources[relative]=root/relative
        cached=sys.modules.get('context_time_travel.'+name)
        if cached is not None and Path(cached.__file__).resolve()!=sources[relative]:
            raise ValueError('Cached COW identity validator belongs to another checkout')
    before={name:hashlib.sha256(p.read_bytes()).hexdigest() for name,p in sources.items()}
    example_path=None if examples_file is None else Path(examples_file).resolve(strict=True)
    example_bytes=None if example_path is None else example_path.read_bytes()
    resolution=module.resolve_parent(proposal['next_parent'],Path(version_file).resolve(strict=True),
        Path(profile_file).resolve(strict=True),artifact_roots=artifact_roots,state_policy=state_policy,
        base_model=base_model,checkpoint_file=checkpoint_file,
        examples=None if example_bytes is None else json.loads(example_bytes))
    for name in ('llama_dense_backend','qwen35_lora'):
        cached=sys.modules.get('context_time_travel.'+name)
        if cached is not None and Path(cached.__file__).resolve()!=root/('experimental/branching_context/src/context_time_travel/'+name+'.py'):
            raise ValueError('COW identity validator imported a different source checkout')
    if (any(p.read_bytes()!=raw for p,raw in zip(paths,original))
            or any(hashlib.sha256(p.read_bytes()).hexdigest()!=before[name] for name,p in sources.items())
            or (example_path is not None and example_path.read_bytes()!=example_bytes)):
        raise ValueError('Frozen proposal, source, evaluations or selected resume stream changed')
    value=dict(schema=1,kind='sss.resolved-learning-parent.v1',status='RESOLVED',
        proposal_id=proposal['proposal_id'],working_decision=proposal['working_decision'],
        strict_preservation_status=proposal['strict_preservation_status'],pcc_resolution=resolution,
        frozen_input_sha256={name:hashlib.sha256(raw).hexdigest() for name,raw in zip(('proposal','baseline','parent','candidate'),original)},
        pcc_source_sha256=before,adapter_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        private_paths=True,gpu_used=False,dispatched=False,promoted=False)
    value['resolution_id']=digest(value);return value


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('pcc-root','proposal','baseline','parent','candidate','version','profile','output'):
        parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--artifact-root',type=Path,action='append',required=True)
    parser.add_argument('--base-model',type=Path);parser.add_argument('--checkpoint',type=Path)
    parser.add_argument('--state-policy',choices=('fresh','resume'),required=True)
    parser.add_argument('--examples',type=Path)
    args=parser.parse_args(argv)
    if args.output.exists():parser.error('Resolution output already exists; inspect it instead of overwriting')
    try:
        value=resolve_proposal(args.pcc_root,args.proposal,args.baseline,args.parent,args.candidate,args.version,args.profile,
            artifact_roots=args.artifact_root,state_policy=args.state_policy,base_model=args.base_model,
            checkpoint_file=args.checkpoint,examples_file=args.examples)
        descriptor=os.open(args.output,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        with os.fdopen(descriptor,'wb') as stream:
            stream.write((json.dumps(value,indent=2,allow_nan=False)+'\n').encode());stream.flush();os.fsync(stream.fileno())
    except (ValueError,OSError,KeyError,TypeError,RuntimeError) as error:
        parser.exit(2,'Cannot resolve proposed parent: '+str(error)+'\n')
    print(json.dumps(dict(status=value['status'],working_decision=value['working_decision'],
                         resolution_id=value['resolution_id'],gpu_used=False,dispatched=False,promoted=False)))
    return 0


if __name__=='__main__':raise SystemExit(main())
