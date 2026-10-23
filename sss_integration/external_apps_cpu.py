"""Host runner for real application protocol fixtures, without a model or GPU."""
from pathlib import Path
import argparse,json,os,subprocess,time
from sss.records import digest

def run(root,apps):
    root=Path(root);root.mkdir(mode=0o700,parents=True,exist_ok=False);results=[]
    script=Path(__file__).with_name('external_apps_fixture.py').resolve()
    for app in ('codex','opencode','pi'):
        work=root/app;work.mkdir(mode=0o700);(work/'app.py').write_text('def double(n):\n    return n\n')
        command=['bwrap','--unshare-all','--die-with-parent','--new-session','--cap-drop','ALL','--clearenv']
        for p in ('/usr','/lib','/lib64','/bin'):
            if Path(p).exists():command+=['--ro-bind',p,p]
        command+=['--proc','/proc','--dev','/dev','--tmpfs','/tmp','--ro-bind',str(Path(apps).resolve()),'/apps','--ro-bind',str(script),'/runner.py','--bind',str(work),'/work','--chdir','/work','--setenv','PATH','/usr/bin:/bin','--setenv','LANG','C.UTF-8','--','python3','/runner.py',app]
        started=time.monotonic()
        try:p=subprocess.run(command,capture_output=True,text=True,timeout=110)
        except subprocess.TimeoutExpired as error:raise RuntimeError('Owned application fixture timed out; namespace must settle') from error
        (root/(app+'.stdout')).write_text(p.stdout);(root/(app+'.stderr')).write_text(p.stderr)
        changed=(work/'app.py').read_text()=='def double(n):\n    return 2*n\n'
        notes=(work/'notes.txt').is_file() and (work/'notes.txt').read_text()=='read, write, edit, verify\n'
        row=dict(app=app,passed=p.returncode==0 and changed and notes,exit_code=p.returncode,repair_verified=changed,write_verified=notes,seconds=time.monotonic()-started,model_inference=False)
        row['evidence_sha256']=digest(row);results.append(row);print(json.dumps(row),flush=True)
    (root/'results.json').write_text(json.dumps(results,indent=2)+'\n')
    return all(r['passed'] for r in results)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--apps',required=True);a=p.parse_args();raise SystemExit(0 if run(a.output,a.apps) else 1)
