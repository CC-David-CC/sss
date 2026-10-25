"""Discover and run S3's opt-in software-machinery integration checks."""
import argparse,json,runpy,sys

SUITES={
    'learning-rounds-cpu':dict(module='sss_integration.learning_rounds_cpu',gpu_required=False,
        description='Real tiny native training/evaluation over durable rounds, both CLIs, restart, no-gain parent selection and private preservation',
        score_scope='Synthetic classifier integration fixture; not a model capability score'),
    'lora-policies-cpu':dict(module='sss_integration.lora_policy_cpu',gpu_required=False,
        description='Registered LoRA AdamW continuation, fresh blocks, partial batches and frozen retries through both clients',
        score_scope='Native mechanics; no language-quality claim'),
    'registered-lora-model':dict(module='sss_integration.registered_lora_model',gpu_required=True,
        description='Prepare checked practice, then qualify registered actual-model LoRA resume against uninterrupted native training',
        score_scope='Owner-configured actual-model integration, not held-out learning; prepare allocates no GPU'),
    'parent-binding-cpu':dict(module='sss_integration.parent_resolution_cpu',gpu_required=False,
        description='Actual native parents and both CLI SHA guards with explicitly controlled S3 decision fixtures',
        score_scope='Native transport and controlled decision mechanics, not measured model learning'),
}


def catalogue():
    return dict(schema=1,kind='sss.machinery-suite-catalog.v1',
        suites=[dict(id=key,**value,counts_toward_model_mastery=False) for key,value in SUITES.items()],
        part_of_frozen_68_update_comparison=False,starts_work_on_listing=False)


def main(argv=None):
    parser=argparse.ArgumentParser(prog='sss machinery',description=__doc__)
    sub=parser.add_subparsers(dest='action',required=True)
    sub.add_parser('list',help='List checks and their qualification scopes without loading BW, PCC, NumPy or a model')
    run=sub.add_parser('run',help='Run one explicitly selected suite; remaining options belong to that suite')
    run.add_argument('suite',choices=SUITES)
    args,remaining=parser.parse_known_args(argv)
    if args.action=='list':
        if remaining:parser.error('list takes no additional arguments')
        print(json.dumps(catalogue(),indent=2));return 0
    original=sys.argv
    try:
        module=SUITES[args.suite]['module'];sys.argv=[module,*remaining]
        runpy.run_module(module,run_name='__main__')
    finally:sys.argv=original
    return 0


if __name__=='__main__':raise SystemExit(main())
