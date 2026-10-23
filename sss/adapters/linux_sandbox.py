"""Optional disposable Linux fixture boundary, not an agent workflow runtime.

The host chooses argv and workspace. Real applications retain scheduling,
permissions, tool identities and task settlement. No host home or credentials
are mounted in the fixture. Networking is confined to the new namespace.
"""
from pathlib import Path
import hashlib
import json
import os
import shutil
import signal
import subprocess
import tempfile
import time
from sss.records import digest

class EnvironmentUnavailable(RuntimeError):pass

class LinuxSandbox:
    def __init__(self,workspace,*,output_limit=262144):
        if os.name!='posix' or not shutil.which('bwrap'):raise EnvironmentUnavailable('Linux bubblewrap is required')
        self.workspace=Path(workspace).resolve(strict=True)
        if not self.workspace.is_dir() or self.workspace==Path('/'):raise ValueError('Owned fixture directory required')
        self.output_limit=output_limit
    def command(self,argv):
        if type(argv) is not list or not argv or any(type(v) is not str or '\0' in v for v in argv):raise ValueError('Explicit argument vector required')
        command=['bwrap','--unshare-all','--die-with-parent','--new-session','--cap-drop','ALL','--clearenv']
        for path in ('/usr','/lib','/lib64','/bin'):
            if Path(path).exists():command+=['--ro-bind',path,path]
        command+=['--proc','/proc','--dev','/dev','--tmpfs','/tmp','--bind',str(self.workspace),'/work','--chdir','/work',
                  '--setenv','PATH','/usr/bin:/bin','--setenv','HOME','/work','--setenv','LANG','C.UTF-8',
                  '--setenv','PYTHONDONTWRITEBYTECODE','1','--',*argv]
        return command
    def run(self,argv,*,timeout=15):
        if not 0<timeout<=120:raise ValueError('Bounded fixture timeout required')
        before=inventory(self.workspace);started=time.monotonic()
        # Files bound memory use even if a tested program emits excessive output.
        with tempfile.TemporaryDirectory(prefix='sss-observation-') as scratch:
            out=Path(scratch)/'stdout';err=Path(scratch)/'stderr'
            def limits():
                import resource
                resource.setrlimit(resource.RLIMIT_FSIZE,(16*1024**2,16*1024**2))
                resource.setrlimit(resource.RLIMIT_NOFILE,(128,128))
                resource.setrlimit(resource.RLIMIT_CORE,(0,0))
            with out.open('wb') as stdout,err.open('wb') as stderr:
                process=subprocess.Popen(self.command(argv),stdout=stdout,stderr=stderr,start_new_session=True,preexec_fn=limits)
                timed_out=False
                try:process.wait(timeout=timeout)
                except subprocess.TimeoutExpired:
                    timed_out=True
                    try:os.killpg(process.pid,signal.SIGKILL)
                    except ProcessLookupError:pass
                    process.wait()
            raw_out=out.read_bytes();raw_err=err.read_bytes()
        row=dict(schema=2,argv=argv,exit_code=process.returncode,timed_out=timed_out,
                 stdout=raw_out[:self.output_limit].decode('utf-8',errors='replace'),stderr=raw_err[:self.output_limit].decode('utf-8',errors='replace'),
                 stdout_sha256=hashlib.sha256(raw_out).hexdigest(),stderr_sha256=hashlib.sha256(raw_err).hexdigest(),
                 output_truncated=len(raw_out)>self.output_limit or len(raw_err)>self.output_limit,
                 before=before,after=inventory(self.workspace),elapsed_seconds=time.monotonic()-started,
                 settled=process.poll() is not None,scope='disposable Linux namespace; actual filesystem/process effects')
        row['evidence_sha256']=digest(row)
        if row['exit_code']!=0 and row['stderr'].startswith('bwrap:'):raise EnvironmentUnavailable(row['stderr'])
        return row

def inventory(root):
    root=Path(root).resolve(strict=True);rows={}
    for path in sorted(root.rglob('*')):
        relative=path.relative_to(root).as_posix()
        if path.is_symlink():rows[relative]=dict(kind='symlink',target=os.readlink(path));continue
        if path.is_file():
            if not path.resolve(strict=True).is_relative_to(root):raise ValueError('Fixture escaped its root')
            rows[relative]=dict(kind='file',sha256=hashlib.sha256(path.read_bytes()).hexdigest(),mode=path.stat().st_mode&0o777,size=path.stat().st_size)
    return rows

def read_owned(root,name):
    root=Path(root).resolve(strict=True);path=root/name
    if path.is_symlink() or not path.resolve(strict=True).is_relative_to(root):raise ValueError('Cannot read an escaped fixture file')
    return path.read_bytes()
