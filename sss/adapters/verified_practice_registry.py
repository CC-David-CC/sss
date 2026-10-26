"""Owner-installed exact BW lesson membership; no training, scoring or dispatch.

Student requests name installed lesson IDs. They cannot provide paths, checker
modules, approvals, or a weaker evaluation policy through this boundary.
"""
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import stat

from sss.records import digest

_KIND = 'sss.verified-bw-practice-registry.v1'
_ROW = {'owner', 'renderer', 'export_directory', 'export_id', 'lesson_id',
        'failure_capture_id', 'correction_capture_id'}
_HASH = re.compile(r'[a-f0-9]{64}\Z')
_MAX_BYTES = 16 * 1024**2
_MAX_LESSONS = 4096


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _private_config(path):
    path = Path(path)
    if not path.is_absolute():
        raise ValueError('Absolute owner registry path required')
    path = Path(os.path.abspath(path))
    required = ('O_NOFOLLOW','O_DIRECTORY','O_CLOEXEC','O_NONBLOCK')
    if any(not hasattr(os,key) for key in required) or os.name != 'posix':
        raise ValueError('Owner registry needs the POSIX no-follow file boundary')
    descriptors = []
    chain = []
    key = lambda row: (row.st_dev,row.st_ino,row.st_size,row.st_mtime_ns,row.st_ctime_ns,row.st_mode,row.st_nlink,row.st_uid)
    try:
        parent = os.open(path.anchor,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC)
        descriptors.append(parent)
        for name in path.parts[1:-1]:
            child = os.open(name,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=parent)
            descriptors.append(child);chain.append((parent,name,child));parent=child
        descriptor=os.open(path.name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC,dir_fd=parent)
        descriptors.append(descriptor);info=os.fstat(descriptor)
        if (not stat.S_ISREG(info.st_mode) or info.st_uid!=os.getuid()
                or info.st_nlink!=1 or info.st_mode&0o077 or not 0<info.st_size<=_MAX_BYTES):
            raise ValueError('Bounded private owned registry file required')
        chunks=[];count=0
        while True:
            data=os.read(descriptor,min(65536,_MAX_BYTES+1-count))
            if not data:break
            chunks.append(data);count+=len(data)
            if count>_MAX_BYTES:raise ValueError('Owner registry exceeds byte bound')
        raw=b''.join(chunks);after=os.fstat(descriptor)
        current=os.stat(path.name,dir_fd=parent,follow_symlinks=False)
        if key(info)!=key(after) or key(after)!=key(current) or len(raw)!=info.st_size:
            raise ValueError('Owner registry changed during descriptor read')
        for base,name,child in chain:
            held=os.fstat(child);current=os.stat(name,dir_fd=base,follow_symlinks=False)
            if not stat.S_ISDIR(current.st_mode) or (held.st_dev,held.st_ino)!=(current.st_dev,current.st_ino):
                raise ValueError('Owner registry ancestor changed during descriptor read')
    except OSError as error:
        raise ValueError('Owner registry descriptor or ancestor is unavailable') from error
    finally:
        for descriptor in reversed(descriptors):os.close(descriptor)
    def pairs(items):
        result = {}
        for name, value in items:
            if name in result:
                raise ValueError('Duplicate registry field')
            result[name] = value
        return result
    def reject(value):
        raise ValueError('Nonfinite registry value')
    try:
        config = json.loads(raw, object_pairs_hook=pairs, parse_constant=reject)
    except (UnicodeError, RecursionError) as error:
        raise ValueError('Invalid bounded owner registry JSON') from error
    if (type(config) is not dict or set(config) != {'schema', 'kind', 'registrations'}
            or type(config['schema']) is not int or config['schema'] != 1
            or config['kind'] != _KIND or type(config['registrations']) is not list
            or not 1 <= len(config['registrations']) <= _MAX_LESSONS):
        raise ValueError('Closed owner verified-practice registry required')
    # Reject nonfinite overflow numbers, unsupported JSON types and malformed rows
    # before any export is opened or an optional runtime is imported.
    json.dumps(config, allow_nan=False)
    for row in config['registrations']:
        if type(row) is not dict or set(row) != _ROW:
            raise ValueError('Exact installed export registration required')
        if type(row['owner']) is not dict or row['owner'].get('kind') != 'bw-artifact-practice-v1':
            raise ValueError('Unknown practice provider; arbitrary modules are unsupported')
        renderer = row['renderer']
        renderer_fields = {'schema','kind','model_contract_id','renderer_sha256','tokenizer_sha256',
            'maximum_tokens','stop_token_ids','representation','adapter_sha256','system_sha256'}
        if (type(renderer) is not dict or set(renderer) != renderer_fields
                or type(renderer['schema']) is not int or renderer['schema'] != 1
                or renderer['kind'] != 'pcc-final-artifact-through-eos-renderer-v1'
                or renderer['representation'] != 'final-artifact-v1'
                or type(renderer['maximum_tokens']) is not int or not 1 <= renderer['maximum_tokens'] <= 131072
                or type(renderer['stop_token_ids']) is not list or not renderer['stop_token_ids']
                or any(type(v) is not int or not 0 <= v < 2**31 for v in renderer['stop_token_ids'])
                or sorted(set(renderer['stop_token_ids'])) != renderer['stop_token_ids']
                or any(type(renderer[k]) is not str or not _HASH.fullmatch(renderer[k])
                    for k in ('model_contract_id','renderer_sha256','tokenizer_sha256','adapter_sha256','system_sha256'))):
            raise ValueError('Exact artifact renderer registration required')
        for key in ('export_id', 'lesson_id', 'failure_capture_id', 'correction_capture_id'):
            if type(row[key]) is not str or not _HASH.fullmatch(row[key]):
                raise ValueError('Owner-pinned export, lesson and capture identities required')
        if type(row['export_directory']) is not str or not Path(row['export_directory']).is_absolute():
            raise ValueError('Absolute owner export path required')
    return path, raw, config


def _load_registration(row, components, model_contract_id):
    # Closed factory: this optional module is the only implementation selected by
    # the owner schema. No request can import a module or choose a checker.
    from sss.adapters.bw_verified_practice import BWArtifactPractice, PCCArtifactRenderer, read_export
    owner = BWArtifactPractice.from_descriptor(row['owner'])
    if owner.model_contract_id != model_contract_id:
        raise ValueError('Installed practice belongs to another model contract')
    bound = row['renderer']
    renderer = PCCArtifactRenderer(components, model_contract_id=model_contract_id,
        tokenizer_sha256=bound['tokenizer_sha256'], maximum_tokens=bound['maximum_tokens'],
        stop_token_ids=bound['stop_token_ids'])
    if renderer.binding() != bound:
        raise ValueError('Installed renderer differs from actual model rendering')
    exported = read_export(row['export_directory'], owner=owner,
        expected_export_id=row['export_id'], correction_capture_id=row['correction_capture_id'],
        failure_capture_id=row['failure_capture_id'], renderer=renderer)
    lesson = exported.lesson
    if (exported.lesson_id != row['lesson_id'] or digest(lesson) != row['lesson_id']
            or lesson.get('model_contract_id') != model_contract_id
            or lesson.get('scope') != 'owned-training'):
        raise ValueError('Installed exact lesson differs from verified export')
    return dict(export_id=exported.export_id, lesson_id=exported.lesson_id,
                owner=owner.binding(), renderer=renderer.binding(), export=exported.binding()), lesson


class InstalledBWPractice:
    """Immutable approved membership for an owner configured learning evaluator.

    Installation is a separate privileged driver action. A successful check or
    client-supplied verification flag does not add membership. This adapter does
    not replace the required target/workflow/retention evaluation panels.
    """
    def __init__(self, path, *, components, model_contract_id):
        if type(model_contract_id) is not str or not _HASH.fullmatch(model_contract_id):
            raise ValueError('Exact serving model contract required')
        self._path, self._raw, self._config = _private_config(path)
        self._components = components
        self._model = model_contract_id
        self._source = _sha(__file__)
        self._registrations, self._lessons = self._materialize()
        self._binding = dict(schema=1, kind=_KIND, model_contract_id=model_contract_id,
            config_sha256=hashlib.sha256(self._raw).hexdigest(),
            registry_implementation_sha256=self._source,
            registrations=copy.deepcopy(self._registrations),
            checked_practice_lesson_ids=sorted(self._lessons))

    def _materialize(self):
        entries, lessons = [], {}
        exports, captures = set(), set()
        for row in self._config['registrations']:
            # Duplicate approval entries are refused, not silently collapsed.
            if row['export_id'] in exports or row['correction_capture_id'] in captures:
                raise ValueError('Duplicate installed export/correction capture')
            exports.add(row['export_id']); captures.add(row['correction_capture_id'])
            entry, lesson = _load_registration(row, self._components, self._model)
            if row['lesson_id'] in lessons:
                raise ValueError('Duplicate installed lesson identity')
            entries.append(entry); lessons[row['lesson_id']] = copy.deepcopy(lesson)
        return entries, lessons

    def binding(self):
        return copy.deepcopy(self._binding)

    def lessons(self):
        self.verify()
        return [copy.deepcopy(self._lessons[key]) for key in sorted(self._lessons)]

    def verify(self):
        path, raw, config = _private_config(self._path)
        if path != self._path or raw != self._raw or config != self._config or _sha(__file__) != self._source:
            raise ValueError('Installed registry or implementation changed; create a new policy/baseline')
        registrations, lessons = self._materialize()
        if registrations != self._registrations or lessons != self._lessons:
            raise ValueError('Original export proof, rendering or lesson bytes changed')

    def validate_lessons(self, records, previous_report=None):
        self.verify()
        if type(records) is not list or not 1 <= len(records) <= _MAX_LESSONS:
            raise ValueError('Explicit bounded installed lesson selection required')
        seen = set()
        for record in records:
            if type(record) is not dict or not {'lesson_id', 'lesson'} <= set(record):
                raise ValueError('Actual stored lesson records required')
            identity = record['lesson_id']
            if (type(identity) is not str or identity in seen or identity not in self._lessons
                    or type(record['lesson']) is not dict or self._lessons[identity] != record['lesson']
                    or digest(record['lesson']) != identity):
                raise ValueError('Lesson is not exact approved membership of this installed provider')
            seen.add(identity)
