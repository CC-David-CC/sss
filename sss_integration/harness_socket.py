"""Run one actual installed client in an owned world against a fixed model port.

This optional integration adapter retains original client events and transport
operations. Task checking, host workflow authority and model leases stay outside.
"""
import hashlib
import json
import subprocess
from pathlib import Path, PurePosixPath

from sss.adapters.linux_sandbox import LinuxSandbox
from sss.records import digest
from .harness_pins import NPM_PINS, HERMES_REVISION, CLIENTS
from .model_socket import ModelSocket, write_new


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class SocketClientSandbox(LinuxSandbox):
    def __init__(self, work, *, prefix, endpoint, source, hermes_source=None):
        super().__init__(work)
        self.prefix, self.endpoint, self.source = prefix, endpoint, source
        self.hermes_source = hermes_source

    def command(self, argv):
        command=super().command(argv);at=command.index('--')
        mounts=['--ro-bind',str(self.prefix),'/tools','--ro-bind',str(self.endpoint),'/model.sock']
        for name,target in [('external_apps_fixture.py','/client_config.py'),('model_socket.py','/model_socket.py'),
                            ('socket_harness_client.py','/client.py')]:
            mounts+=['--ro-bind',str(self.source/name),target]
        if self.hermes_source is not None:
            mounts+=['--ro-bind',str(self.hermes_source),'/hermes','--setenv','PYTHONPATH','/hermes',
                     '--setenv','HERMES_HOME','/work/hermes-home','--setenv','HERMES_RUNTIME_DIR','/work/hermes-runtime',
                     '--setenv','TERMINAL_CWD','/work','--setenv','TERMINAL_ENV','local']
        command[at:at]=mounts+['--setenv','SSS_ISOLATED_TRANSPORT_FIXTURE','1']
        return command


def run_client(root, *, app, prefix, port, model, context, instruction, files,
               backend_identity, operation_id, api_key_file=None, maximum_calls=12, hermes_source=None,
               guidance=''):
    if app not in CLIENTS or type(context) is not int or not 1024 <= context <= 131072:
        raise ValueError('Supported pinned client and explicit bounded context required')
    if not instruction or type(files) is not dict or not files:
        raise ValueError('Explicit task instruction and prepared files required')
    if type(guidance) is not str or len(guidance)>4096:
        raise ValueError('Bounded harness instruction guidance required')
    if app=='pi' and context<=4096:
        raise ValueError('Pinned pi reserves 4096 context tokens; this declaration cannot leave useful output room')
    if backend_identity.get('evidence_kind') not in ('synthetic_transport','pcc_native','native_llama_cpp'):
        raise ValueError('Explicit backend evidence classification required')
    prefix=Path(prefix).resolve(strict=True)
    if app=='hermes':
        hermes_source=Path(hermes_source).resolve(strict=True)
        revision=subprocess.check_output(['git','-C',str(hermes_source),'rev-parse','HEAD'],text=True).strip()
        if revision!=HERMES_REVISION or subprocess.check_output(['git','-C',str(hermes_source),'status','--porcelain'],text=True):
            raise ValueError('Clean pinned Hermes source required')
        package,version='NousResearch/hermes-agent',revision
        lock=hermes_source/'uv.lock'
    else:
        if hermes_source is not None:raise ValueError('Hermes source is only valid for Hermes')
        package,version=NPM_PINS[app]
        installed=json.loads((prefix/'node_modules'/package/'package.json').read_text())
        if installed['name']!=package or installed['version']!=version:
            raise ValueError('Installed client differs from its pin')
        lock=prefix/'package-lock.json'
    if not lock.is_file():raise ValueError('Retain the installed dependency lock')
    root=Path(root).absolute();root.mkdir(mode=0o700,parents=True,exist_ok=False)
    work=root/'world';work.mkdir(mode=0o700)
    for name,raw in files.items():
        path=PurePosixPath(name)
        if path.is_absolute() or '..' in path.parts or name in ('instruction.txt','.') or type(raw) is not bytes:
            raise ValueError('Owned relative fixture bytes required')
        target=work/str(path);target.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
        with target.open('xb') as stream:
            stream.write(raw)
    rendered=instruction+('\n\nExecution guidance:\n'+guidance if guidance else '')
    (work/'instruction.txt').write_text(rendered)
    source=Path(__file__).resolve().parent
    manifest=dict(schema=1,app=app,package=package,version=version,package_lock_sha256=sha(lock),
        model_alias=model,context=context,output_bound=512,maximum_model_calls=maximum_calls,
        operation_id=operation_id,backend_identity=backend_identity,
        instruction_sha256=hashlib.sha256(instruction.encode()).hexdigest(),
        guidance_sha256=hashlib.sha256(guidance.encode()).hexdigest(),
        rendered_instruction_sha256=hashlib.sha256(rendered.encode()).hexdigest(),
        fixture_sha256={name:hashlib.sha256(raw).hexdigest() for name,raw in files.items()},
        source_sha256={name:sha(source/name) for name in ('harness_socket.py','harness_pins.py','model_socket.py','socket_harness_client.py','external_apps_fixture.py')},
        sampling_policy='Fill omitted temperature=0 and seed=0; reject changes',
        authority='Original client tool loop inside disposable Linux namespaces; fixed model endpoint only',
        task_success_inferred=False)
    write_new(root/'manifest.json',manifest)
    endpoint=ModelSocket(root/'endpoint',port=port,model=model,operation_id=operation_id,
        api_key_file=api_key_file,maximum_calls=maximum_calls,output_bound=512,timeout=90).start()
    boundary=None
    try:
        sandbox=SocketClientSandbox(work,prefix=prefix,endpoint=endpoint.path,source=source,hermes_source=hermes_source)
        boundary=sandbox.run(['python3','/client.py',app,'--model',model,'--context',str(context)],timeout=110)
        write_new(root/'boundary-private.json',boundary)
    finally:
        endpoint.close()
    receipt=work/'client-receipt.json'
    client=json.loads(receipt.read_text()) if receipt.is_file() else None
    denied_discovery=[r['operation_id'] for r in endpoint.records if r['method']=='GET' and r['outcome']=='rejected']
    transport_ok=bool(boundary and boundary['settled'] and not boundary['timed_out'] and boundary['exit_code']==0
        and client and client['client_exit_code']==0 and not client['client_timed_out'] and endpoint.calls>0
        and not endpoint.stopped and all(r['outcome']=='complete' or r['operation_id'] in denied_discovery for r in endpoint.records))
    result=dict(schema=1,app=app,version=version,operation_id=operation_id,
        manifest_sha256=digest(manifest),backend_identity=backend_identity,
        transport_complete=transport_ok,forwarded_model_requests=endpoint.calls,
        original_transport_operations=[r['operation_id'] for r in endpoint.records],
        denied_discovery_operations=denied_discovery,
        uncertain=any(r['outcome']=='uncertain' for r in endpoint.records),
        boundary_settled=bool(boundary and boundary['settled']),client=client,
        boundary_receipt_sha256=boundary['evidence_sha256'] if boundary else None,
        task_success_inferred=False,promoted=False)
    write_new(root/'result.json',result)
    return result
