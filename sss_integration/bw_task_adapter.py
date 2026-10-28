"""Materialize S³'s public shell fixture for a BW tooling qualification run.

This is a fixture adapter, not an evaluation or workflow runtime. The command
and its inputs are intentionally visible to the model. S³'s independent host
checker remains authoritative for grading a captured task artifact.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

from sss.suites.code_foundations import cases


_PUBLIC_BW_TASKS = {
    'shell.failure_status': {
        'source_path': 'check.sh',
        'fixture_files': {
            'tests/ready.txt': b'READY\n',
            'tests/not-ready.txt': b'not ready\n',
        },
        # Keep this exact command in sync with the BW command-evidence policy.
        'test_command': (
            'sh check.sh tests/ready.txt && '
            'if sh check.sh tests/not-ready.txt; then exit 1; '
            'else status=$?; test "$status" -ne 0; fi'
        ),
    },
    'shell.quoted_filename': {
        'source_path': 'copy.sh',
        'fixture_files': {
            'source one.txt': 'one\nUnicode: α\n'.encode('utf-8'),
            'semi;colon.txt': 'one\nUnicode: α\n'.encode('utf-8'),
        },
        'test_command': (
            "sh copy.sh 'source one.txt' 'dest two.txt' && "
            "cmp -s 'source one.txt' 'dest two.txt' && "
            "sh copy.sh 'semi;colon.txt' 'literal $name.txt' && "
            "cmp -s 'semi;colon.txt' 'literal $name.txt'"
        ),
    },
}


def prepare_public_bw_task(case_id: str, project_root: str | Path) -> dict:
    """Create a self-contained, visible S³ task fixture for an existing BW run.

    The destination must be a new or empty ordinary directory. Returned paths
    are relative to that directory, so the declared check command works inside
    BW's isolated workspace and never points at a host-only checker.
    """
    spec = _PUBLIC_BW_TASKS.get(case_id)
    if spec is None:
        raise ValueError(f'no public BW tooling fixture registered for {case_id!r}')
    case = next((row for row in cases() if row.id == case_id), None)
    source_path = spec['source_path']
    if case is None or set(case.before) != {source_path}:
        raise ValueError('registered BW fixture no longer matches its S³ source case')

    root = Path(project_root).absolute()
    if any(parent.is_symlink() for parent in (root, *root.parents)):
        raise ValueError('project path cannot contain a symlink')
    root.mkdir(parents=True, exist_ok=True)
    if any(root.iterdir()):
        raise ValueError('project root must be empty before fixture materialization')

    source_files = dict(case.before)
    all_files = {**source_files, **spec['fixture_files']}
    for relative, content in all_files.items():
        rel = Path(relative)
        if rel.is_absolute() or '..' in rel.parts or not content:
            raise ValueError('fixture contains an invalid path or empty file')
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content.encode('utf-8') if isinstance(content, str) else content)

    return {
        'case_id': case_id,
        'task': case.request,
        'read_paths': [source_path],
        'edit_paths': [source_path],
        'test_command': spec['test_command'],
        'fixture_sha256': {
            name: hashlib.sha256((root / name).read_bytes()).hexdigest()
            for name in sorted(all_files)
        },
        'qualification_only': True,
        'visible_to_model': True,
        'host_checker_remains_authoritative': True,
    }
