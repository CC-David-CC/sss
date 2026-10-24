"""Run one real client inside its prepared world against a model-only socket."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def main():
    if os.environ.get('SSS_ISOLATED_TRANSPORT_FIXTURE') != '1' or Path.cwd() != Path('/work'):
        raise RuntimeError('Use the owned Linux sandbox launcher')
    sys.path.insert(0, '/')
    from client_config import configuration
    from model_socket import LoopbackRelay
    parser=argparse.ArgumentParser();parser.add_argument('app',choices=['codex','opencode','pi','hermes','qwen','dsh'])
    parser.add_argument('--model',required=True);parser.add_argument('--context',required=True,type=int)
    args=parser.parse_args()
    if not 1024 <= args.context <= 131072:
        raise ValueError('Explicit bounded model context required')
    prompt=Path('/work/instruction.txt').read_text()
    relay=LoopbackRelay('/model.sock',timeout=90).start()
    process=None;timed_out=False;started=time.monotonic()
    try:
        argv=configuration(args.app,relay.port,model=args.model,context=args.context,prompt=prompt,disable_delegation=True,stream_idle_ms=90000)
        process=subprocess.run(argv,cwd='/work',stdin=subprocess.DEVNULL,capture_output=True,text=True,timeout=95)
    except subprocess.TimeoutExpired:
        timed_out=True
    finally:
        relay.close()
    Path('/work/client-events-private.jsonl').write_text(process.stdout if process else '')
    Path('/work/client-stderr-private.txt').write_text(process.stderr if process else '')
    result=dict(schema=1,app=args.app,configured_model=args.model,context=args.context,
        client_exit_code=process.returncode if process else None,client_timed_out=timed_out,
        elapsed_seconds=time.monotonic()-started,task_success_not_inferred_from_exit_code=True)
    Path('/work/client-receipt.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
    return 0 if process and process.returncode==0 and not timed_out else 1


if __name__=='__main__':
    raise SystemExit(main())
