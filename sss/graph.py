"""Version two prerequisite graphs; taxonomy is deliberately not a prerequisite."""
import re
import copy
from .records import digest

_ID = re.compile(r'[a-z][a-z0-9_.-]{0,127}\Z')

def identifier(value):
    if type(value) is not str or not _ID.fullmatch(value):
        raise ValueError('Invalid stable identifier')
    return value

class SkillGraph:
    def __init__(self, document):
        if type(document) is not dict or set(document) != {'schema','name','nodes'} or document['schema'] != 2:
            raise ValueError('Expected skill graph schema 2')
        if not isinstance(document['name'], str) or not document['name']:
            raise ValueError('Graph needs a name')
        if type(document['nodes']) is not list or not 1 <= len(document['nodes']) <= 4096:
            raise ValueError('Graph requires 1..4096 explicit nodes')
        self.nodes = {}
        fields={'id','title','domains','requires','bands','checker','status'}
        for original in document['nodes']:
            if type(original) is not dict or set(original) != fields:
                raise ValueError('Invalid graph node fields')
            row={k:list(v) if type(v) is list else v for k,v in original.items()}
            key=identifier(row['id'])
            if key in self.nodes: raise ValueError('Duplicate skill')
            if type(row['title']) is not str or not row['title']: raise ValueError('Missing title')
            for field in ('domains','requires','bands'):
                values=row[field]
                if type(values) is not list or len(values)!=len(set(values)):
                    raise ValueError('Expected unique '+field)
                for value in values: identifier(value)
            if not row['domains'] or not row['bands']: raise ValueError('Missing domain or band')
            if row['status'] not in ('planned','implemented'): raise ValueError('Unknown coverage state')
            if row['checker'] is not None: identifier(row['checker'])
            if row['status']=='implemented' and row['checker'] is None: raise ValueError('Implemented node needs a checker')
            self.nodes[key]=row
        self.order=[]; active=set(); done=set()
        def visit(key):
            if key not in self.nodes: raise ValueError('Unknown prerequisite: '+key)
            if key in active: raise ValueError('Prerequisite cycle')
            if key in done:return
            active.add(key)
            for parent in self.nodes[key]['requires']:visit(parent)
            active.remove(key);done.add(key);self.order.append(key)
        for key in sorted(self.nodes):visit(key)
        self.name=document['name']
        self.identity=digest(self.document())
    def document(self):
        return dict(schema=2,name=self.name,nodes=[copy.deepcopy(self.nodes[k]) for k in sorted(self.nodes)])
    def prerequisites(self, key):
        if digest(self.document())!=self.identity:raise ValueError('Graph changed after it was bound')
        identifier(key)
        if key not in self.nodes:raise ValueError('Unknown skill')
        result=set()
        def visit(node):
            for parent in self.nodes[node]['requires']:
                if parent not in result:result.add(parent);visit(parent)
        visit(key)
        return tuple(k for k in self.order if k in result)
    def readiness(self, key, qualified):
        missing=[p for p in self.prerequisites(key) if p not in qualified]
        return dict(skill_id=key,ready=not missing,missing=missing,
                    diagnostic_allowed=True,grants_capabilities=False)
