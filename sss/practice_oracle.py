"""Owner-installed synthetic practice cases. No execution or optional runtime imports."""
from dataclasses import dataclass
import hashlib
import json
import math
import re
from sss.records import canonical, digest

FAMILY = 'affine-clamp-fold-v1'
MAX_OUTPUT = 262144

def strict_json(raw):
    def pairs(items):
        out = {}
        for key, value in items:
            if key in out:
                raise ValueError('duplicate JSON key')
            out[key] = value
        return out
    def reject(value):
        raise ValueError('nonfinite JSON value')
    def floating(value):
        parsed = float(value)
        if not math.isfinite(parsed):
            reject(value)
        return parsed
    if type(raw) is bytes:
        raw = raw.decode('utf8', errors='strict')
    try:
        return json.loads(raw, object_pairs_hook=pairs, parse_constant=reject, parse_float=floating)
    except (RecursionError, OverflowError) as error:
        raise ValueError('JSON nesting or numeric representation exceeds safe bounds') from error

def _int(value):
    if type(value) is not int or not -1000000 <= value <= 1000000:
        raise ValueError('bounded JSON integer excluding Boolean required')

def _rows(rows):
    if type(rows) is not list or not 1 <= len(rows) <= 32:
        raise ValueError('one to32 explicit rows required')
    for row in rows:
        if type(row) is not dict or set(row) != {'values','scale','offset','low','high'}:
            raise ValueError('exact affine-clamp-fold row required')
        if type(row['values']) is not list or len(row['values']) > 64:
            raise ValueError('bounded values list required')
        for value in row['values']:
            _int(value)
        for key in ('scale','offset','low','high'):
            _int(row[key])
        if row['low'] > row['high']:
            raise ValueError('low must not exceed high')
    raw = canonical(rows)
    if len(raw) > 16384:
        raise ValueError('input rows exceed16KiB')
    return raw

@dataclass(frozen=True)
class AffineClampFoldCase:
    case_id: str
    split_id: str
    inputs_json: bytes
    family: str = FAMILY

    def __post_init__(self):
        if type(self.family) is not str or self.family != FAMILY:
            raise ValueError('unsupported owner checker family')
        for name in (self.case_id, self.split_id):
            if type(name) is not str or re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,127}', name) is None:
                raise ValueError('bounded explicit case/split identity required')
        if type(self.inputs_json) is not bytes or len(self.inputs_json) > 16384:
            raise ValueError('immutable bounded canonical JSON bytes required')
        if _rows(strict_json(self.inputs_json)) != self.inputs_json:
            raise ValueError('canonical immutable input rows required')

    @classmethod
    def install(cls, case_id, split_id, rows):
        return cls(case_id, split_id, _rows(rows))

    @property
    def rows(self):
        return strict_json(self.inputs_json)

    @property
    def pins(self):
        value = dict(case_schema=1, family=self.family, case_id=self.case_id, split_id=self.split_id,
                     inputs_sha256=hashlib.sha256(self.inputs_json).hexdigest())
        return dict(value, case_sha256=digest(value))

    def expected(self):
        results = []
        for row in self.rows:
            values = [min(row['high'], max(row['low'], row['scale']*x+row['offset'])) for x in row['values']]
            results.append(dict(values=values, total=sum(values)))
        return dict(results=results, inputs_after=self.rows)

def exact(actual, expected):
    if type(actual) is not type(expected):
        return False
    if type(expected) is dict:
        return set(actual) == set(expected) and all(exact(actual[k],v) for k,v in expected.items())
    if type(expected) is list:
        return len(actual) == len(expected) and all(exact(a,b) for a,b in zip(actual,expected))
    return actual == expected

def grade_observation(case, observation):
    """Grade a trusted adapter's observation; not an untrusted receipt authenticator."""
    if type(case) is not AffineClampFoldCase:
        raise ValueError('installed fixed-family case required')
    witness = observation.get('isolation', {})
    settled = (observation.get('disposition') == 'exited'
               and witness.get('kind') == 'bubblewrap-terminal-v1'
               and witness.get('worker_exited') is True
               and witness.get('namespace_members_after') == []
               and observation.get('output_truncated') is False)
    if not settled:
        return dict(status='unavailable', reason='bounded execution and namespace retirement not proven')
    if observation.get('source_unchanged') is not True:
        return dict(status='unavailable', reason='captured source identity changed or is uncertain')
    if observation.get('captured_execution_source_matches') is not True:
        return dict(status='unavailable', reason='actual BW projected source pin is missing or differs')
    if type(observation.get('exit_code')) is not int or observation['exit_code'] != 0:
        return dict(status='fail', reason='settled student function execution returned nonzero')
    try:
        stdout = observation['stdout']
        if type(stdout) is not str or len(stdout.encode('utf8')) > MAX_OUTPUT:
            raise ValueError('bounded UTF8 JSON output required')
        actual = strict_json(stdout)
        passed = exact(actual, case.expected())
    except (ValueError, TypeError, KeyError, UnicodeError, RecursionError):
        passed = False
    return dict(status='pass' if passed else 'fail',
                reason='' if passed else 'host return-value, strict JSON, exact types or input-preservation check failed')
