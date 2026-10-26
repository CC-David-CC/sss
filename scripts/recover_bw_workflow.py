#!/usr/bin/env python3
"""Explicitly continue one stopped workflow using its original source snapshot."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys
import traceback

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for flag in ('sss-root','api-root','owner-config','candidate','profile','evaluation','output'):
        ap.add_argument('--'+flag,type=Path,required=True)
    ap.add_argument('--producer-owner',type=Path,action='append',default=[])
    ap.add_argument('--case-index',type=int,required=True)
    ap.add_argument('--additional-steps',type=int,required=True)
    ap.add_argument('--allow-original-replay',action='store_true')
    for flag in ('cache-bytes','staging-bytes','minimum-free-bytes'):
        ap.add_argument('--'+flag,type=int,required=True)
    args=ap.parse_args();read=lambda p:json.loads(p.read_bytes())
    original_output=args.evaluation.resolve(strict=True).parent
    if args.output.exists():raise ValueError('Recovery output already exists; inspect that original attempt')
    cfg=read(args.owner_config)
    paths=[args.sss_root,args.api_root,Path(cfg['pcc_root']),
        Path(cfg['pcc_root'])/'experimental/branching_context/src',Path(cfg['bw_root'])]
    sys.path[:0]=[str(p.resolve(strict=True))for p in paths]
    from sss.adapters.workflow_evaluation import BWWorkflowEvaluator
    from sss.adapters.cow_learning import write_once
    from sss.records import canonical,file_sha256,digest
    panel=BWWorkflowEvaluator(args.owner_config)
    intent=read(original_output/'adapter-intent-private.json')
    if panel.identity!=intent['evaluator_id']:raise ValueError('Original evaluator source identity changed')
    candidate=read(args.candidate);profile=read(args.profile)
    if (canonical(candidate)!=canonical(read(original_output/'candidate-selection-private.json'))
            or canonical(profile)!=canonical(read(original_output/'candidate-profile.json'))):
        raise ValueError('Original candidate or execution profile changed')
    # The recorded child is mandatory; optional outer-controller proofs add to it.
    owners=[read(original_output/'child-process-private.json'),*[read(p)for p in args.producer_owner]]
    helper=Path(__file__).resolve().parents[1]/'sss_integration/workflow_recovery.py'
    spec=importlib.util.spec_from_file_location('sss_owner_workflow_recovery',helper)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    try:
        result=module.resume_case(panel,profile,candidate,args.evaluation,args.case_index,args.output,
            producer_identities=owners,additional_steps=args.additional_steps,
            allow_original_replay=args.allow_original_replay,
            storage=dict(cache_bytes=args.cache_bytes,staging_bytes=args.staging_bytes,
                         minimum_free_bytes=args.minimum_free_bytes))
        receipt=dict(status='COMPLETE',result_sha256=digest(result),helper_sha256=file_sha256(helper),
            finished=result['finished'],passed=result['passed'],promoted=False)
        write_once(args.output/'operator-exit-private.json',receipt)
        print(json.dumps(receipt));return 0
    except BaseException as exc:
        if args.output.is_dir():
            write_once(args.output/'operator-exit-private.json',dict(status='NEEDS_REVIEW',
                error=type(exc).__name__+': '+str(exc),automatic_retry=False))
        raise

if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception:traceback.print_exc();raise SystemExit(2)
