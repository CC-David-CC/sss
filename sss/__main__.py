import argparse
import json
from pathlib import Path
from .catalog import catalog,format_tree
from .guard import SkillTree

def main(argv=None):
    import sys
    argv=sys.argv[1:] if argv is None else argv
    if argv and argv[0]=='machinery':
        from .machinery import main as machinery_main
        return machinery_main(argv[1:])
    if argv and argv[0]=='workflows':
        from .workflows import main as workflows_main
        return workflows_main(argv[1:])
    if argv and argv[0]=='explore':
        from .explore_cli import main as explore_main
        return explore_main(argv[1:])
    if argv and argv[0] in ('graph','exercise','school-day','report','teaching-example'):
        from .foundation_cli import main as foundation_main
        return foundation_main(argv)
    if argv[:2]==['bench','tool-use']:
        from .tool_benchmark import main as benchmark
        return benchmark(argv[2:])
    if argv and argv[0]=='init-pcc':
        from .adapters.pcc_init import main as initialize
        return initialize(argv[1:])
    if argv[:2]==['study','harness']:
        from .studies.harness_compare import main as compare_harnesses
        return compare_harnesses(argv[2:])
    if argv[:2]==['study','assessment-growth']:
        from .assessment_growth import main as assessment_growth_main
        return assessment_growth_main(argv[2:])
    if argv[:2]==['study','next-block']:
        from .learning import main as next_block
        return next_block(argv[2:])
    if argv[:2]==['study','ceiling']:
        from .studies.ceiling import main as study
        return study(argv[2:])
    parser=argparse.ArgumentParser(prog='sss',description='Skills³ (S³): Skills, Scoring, Stability')
    sub=parser.add_subparsers(dest='action',required=True)
    p=sub.add_parser('tree',help='Show the broad skill map or a frozen active tree');p.add_argument('--active',type=Path);p.add_argument('--json',action='store_true')
    p=sub.add_parser('verify-tree',help='Require practice and independent validation/blind coverage at every active leaf');p.add_argument('file',type=Path)
    p=sub.add_parser('suite',help='Describe available original tool-use scenarios');p.add_argument('name',choices=['tool-use'])
    sub.add_parser('init-pcc',help='Prepare owned arithmetic replay in an optional PCC store; see init-pcc --help')
    sub.add_parser('study',help='Study commands; see study harness --help, study ceiling --help or study next-block --help')
    sub.add_parser('workflows',help='Existing BW domain recipes; see workflows --help')
    sub.add_parser('machinery',help='Software integration checks, separate from model capability scores; see machinery list')
    sub.add_parser('explore',help='Guided foundations checks; see explore --help')
    sub.add_parser('graph',help='Show the prerequisite graph; see graph --help')
    sub.add_parser('report',help='Write an offline report; see report --help')
    sub.add_parser('bench',help='Run a model-only mock-tool benchmark; see bench tool-use --help')
    args=parser.parse_args(argv)
    if args.action=='tree':value=SkillTree(json.loads(args.active.read_bytes())).describe() if args.active else catalog()
    elif args.action=='verify-tree':value=SkillTree(json.loads(args.file.read_bytes())).describe()
    else:
        from .suites.tool_use import describe
        value=describe()
    print(format_tree(value) if args.action=='tree' and not args.json else json.dumps(value,indent=2,ensure_ascii=False));return 0

if __name__=='__main__':raise SystemExit(main())
