"""Opt-in CPU protocol qualification using installed CLIs in disposable worlds.

This launcher does not install software, call a model, or run an agent workflow.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

from sss.adapters.linux_sandbox import LinuxSandbox
from sss.records import digest


PACKAGES = {'codex': ('@openai/codex', '0.164.0'),
            'opencode': ('@opencode/cli', '2.1.4'),
            'pi': ('@earendil-works/pi-coding-agent', '1.4.0')}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class ProtocolSandbox(LinuxSandbox):
    def __init__(self, workspace, prefix, protocol, script):
        super().__init__(workspace)
        self.prefix, self.protocol, self.script = prefix, protocol, script

    def command(self, argv):
        command = super().command(argv)
        at = command.index('--')
        command[at:at] = ['--ro-bind', str(self.prefix), '/tools', '--ro-bind', str(self.protocol), '/pcc',
                         '--ro-bind', str(self.script), '/runner.py',
                         '--setenv', 'SSS_ISOLATED_TRANSPORT_FIXTURE', '1']
        return command


def run(root, prefixes, pcc):
    prefixes = json.loads(Path(prefixes).read_text())
    assert set(prefixes) == set(PACKAGES), 'Pin all three installed CLI prefixes'
    toolchains = {}
    for app, (package, version) in PACKAGES.items():
        prefix = Path(prefixes[app]).resolve(strict=True)
        actual = json.loads((prefix/'node_modules'/package/'package.json').read_text())
        assert actual['name'] == package and actual['version'] == version, 'Unexpected CLI version: ' + app
        lock = prefix/'package-lock.json'; assert lock.is_file(), 'Retain the installed dependency lock'
        toolchains[app] = dict(package=package, version=version, package_lock_sha256=sha(lock))
        prefixes[app] = prefix
    pcc = Path(pcc).resolve(strict=True)
    source_revision = subprocess.check_output(['git', '-C', str(pcc), 'rev-parse', 'HEAD'], text=True).strip()
    root = Path(root).absolute(); root.mkdir(mode=0o700, parents=True, exist_ok=False)
    assert root.stat().st_uid == os.getuid()
    protocol = root/'pcc-protocol'; (protocol/'serve').mkdir(mode=0o700, parents=True)
    protocol_files = {}
    for name in ('__init__.py', 'frontend.py', 'responses.py'):
        source = pcc/'serve'/name
        target = protocol/'serve'/name
        shutil.copyfile(source, target); protocol_files['serve/'+name] = sha(target)
    script = Path(__file__).with_name('external_apps_fixture.py').resolve(strict=True)
    identity = dict(schema=2, source_revision=source_revision, protocol_files=protocol_files,
                    fixture_sha256=sha(script), launcher_sha256=sha(__file__), toolchains=toolchains,
                    network='new isolated namespace; loopback mock endpoint only',
                    home='new disposable /work; no inherited credentials', real_model_calls=0)
    (root/'manifest.json').write_text(json.dumps(identity, indent=2) + '\n')
    results = []
    for app in PACKAGES:
        work = root/app; work.mkdir(mode=0o700)
        (work/'app.py').write_text('def double(n):\n    return n\n')
        sandbox = ProtocolSandbox(work, prefixes[app], protocol, script)
        receipt = sandbox.run(['python3', '/runner.py', app], timeout=110)
        (root/(app+'-boundary-private.json')).write_text(json.dumps(receipt, indent=2) + '\n')
        result_path = work/'result.json'
        result = json.loads(result_path.read_text()) if result_path.is_file() else dict(app=app, passed=False, missing_result=True)
        result['boundary_settled'] = receipt['settled']
        result['boundary_timed_out'] = receipt['timed_out']
        result['boundary_exit_code'] = receipt['exit_code']
        result['passed'] = bool(result['passed'] and receipt['settled'] and not receipt['timed_out'] and receipt['exit_code'] == 0)
        result['boundary_receipt_sha256'] = receipt['evidence_sha256']
        result['evidence_sha256'] = digest(result)
        results.append(result); print(json.dumps(result), flush=True)
    output = dict(schema=2, manifest=identity, manifest_sha256=digest(identity), results=results,
                  all_passed=all(r['passed'] for r in results), real_model_calls=0,
                  performance_comparison=False, promoted=False)
    (root/'results.json').write_text(json.dumps(output, indent=2) + '\n')
    return output['all_passed']


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, help='New owned private evidence directory')
    parser.add_argument('--prefixes', required=True, help='JSON mapping codex/opencode/pi to pinned installed prefixes')
    parser.add_argument('--pcc-root', required=True, help='Inspected PCC source for its actual Responses formatter')
    args = parser.parse_args()
    raise SystemExit(0 if run(args.output, args.prefixes, args.pcc_root) else 1)
