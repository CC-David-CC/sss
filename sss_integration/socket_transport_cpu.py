"""Exercise the model-only socket with actual CLIs and scripted CPU replies."""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import subprocess
import sys
import threading

from sss.records import digest
from . import external_apps_fixture as fixture_module
from .harness_socket import run_client
from .model_socket import write_new


def run(root, prefixes, pcc_root):
    root=Path(root).absolute();root.mkdir(mode=0o700,parents=True,exist_ok=False)
    prefixes=json.loads(Path(prefixes).read_text());pcc=Path(pcc_root).resolve(strict=True)
    sys.path.insert(0,str(pcc))
    from serve import responses
    from serve.frontend import Event, ToolCall
    fixture_module.responses=responses;fixture_module.Event=Event;fixture_module.ToolCall=ToolCall
    key=root/'host-key-fixture.txt';key.write_text('host-only-socket-fixture-key\n');key.chmod(0o600)
    rows=[]
    for app in ('codex','opencode','pi'):
        fixture=fixture_module.Fixture(app)

        class Backend(BaseHTTPRequestHandler):
            def log_message(self,*args):
                pass
            def do_POST(self):
                try:
                    assert self.headers.get('Authorization')=='Bearer host-only-socket-fixture-key'
                    body=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                    assert body['seed']==0 and body['temperature']==0
                    with fixture.lock:
                        raw=fixture.reply(self.path,body)
                    self.send_response(200);self.send_header('Content-Type','text/event-stream')
                    self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
                except Exception as error:
                    fixture.failures.append(dict(type=type(error).__name__,message=str(error)))
                    self.send_error(400,'Scripted backend contract failed')

        backend=ThreadingHTTPServer(('127.0.0.1',0),Backend)
        thread=threading.Thread(target=backend.serve_forever,daemon=True);thread.start()
        try:
            result=run_client(root/app,app=app,prefix=prefixes[app],port=backend.server_port,
                model='wen-fixture',context=16384,instruction=fixture_module.PROMPT,
                files={'app.py':b'def double(n):\n    return n\n'},
                backend_identity=dict(evidence_kind='synthetic_transport',real_model_calls=0,
                    pcc_source=subprocess.check_output(['git','-C',str(pcc),'rev-parse','HEAD'],text=True).strip()),
                operation_id=digest(['socket-cpu',root.name,app]),api_key_file=key,maximum_calls=5)
        finally:
            backend.shutdown();backend.server_close();thread.join(timeout=3)
        work=root/app/'world'
        repair=(work/'app.py').read_text()=='def double(n):\n    return 2*n\n'
        notes=(work/'notes.txt').is_file() and (work/'notes.txt').read_text()=='read, write, edit, verify\n'
        delegation_absent=True
        if app=='codex' and fixture.requests:
            tools,_,_=responses.request_tools(fixture.requests[0]['body'])
            delegation_absent=not any('agent' in t['name'] or 'spawn' in t['name'] for t in tools or [])
        secret_absent=not any(b'host-only-socket-fixture-key' in p.read_bytes() for p in work.rglob('*')
            if not p.is_symlink() and p.is_file() and p.resolve().is_relative_to(work.resolve()))
        row=dict(result,fixture_passed=bool(result['transport_complete'] and repair and notes
            and len(fixture.requests)==5 and len(fixture.calls)==4 and not fixture.failures
            and secret_absent and delegation_absent),
            repair_verified=repair,write_verified=notes,host_secret_absent_from_world=secret_absent,
            delegation_tools_absent=delegation_absent,actual_tools=[c['name'] for c in fixture.calls],
            failures=fixture.failures,real_model_calls=0,pcc_native_backend_tested=False)
        write_new(root/(app+'-requests-private.json'),fixture.requests)
        rows.append(row);print(json.dumps(row),flush=True)
    report=dict(schema=1,evidence_kind='synthetic_transport_real_host_tools',results=rows,
        all_passed=all(r['fixture_passed'] for r in rows),real_model_calls=0,
        weights_updated=False,promoted=False)
    write_new(root/'results.json',report)
    return report['all_passed']


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',required=True)
    parser.add_argument('--prefixes',required=True);parser.add_argument('--pcc-root',required=True)
    args=parser.parse_args()
    raise SystemExit(0 if run(args.output,args.prefixes,args.pcc_root) else 1)
