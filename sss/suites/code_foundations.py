"""Owned bounded Python/shell tasks, checked by behavior on unseen arguments."""
from dataclasses import dataclass
import ast
import json
from sss.records import digest

@dataclass(frozen=True)
class CodeCase:
    id:str
    language:str
    request:str
    before:dict
    check_program:str
    reference:dict
    skills:tuple

# Checks inspect actual execution in the optional Linux sandbox. They are never
# mounted into a student's workspace before their completed attempt is captured.
def cases():
    return (
        CodeCase('python.sum_empty','python','Repair total(values) so it sums any integer list, including an empty list. Preserve the function name.',
                 {'task.py':'def total(values):\n    answer = values[0]\n    for value in values[1:]:\n        answer += value\n    return answer\n'},
                 'import task\nfor xs in ([],[0],[-3,4,12],list(range(-30,31))):\n assert task.total(xs)==sum(xs),repr(xs)\n',
                 {'task.py':'def total(values):\n    answer = 0\n    for value in values:\n        answer += value\n    return answer\n'},
                 ('code.python.read','code.python.tests','code.python.debug')),
        CodeCase('python.binary_search','python','Implement locate(values, target) for a sorted integer list: return the first matching index, or -1. It must not mutate values.',
                 {'task.py':'def locate(values, target):\n    return -1\n'},
                 'import task\nfor xs in ([],[1],[1,1,2,4,4],list(range(-30,31))):\n for target in range(-32,33):\n  original=list(xs)\n  expected=xs.index(target) if target in xs else -1\n  assert task.locate(xs,target)==expected,(xs,target)\n  assert xs==original\n',
                 {'task.py':'def locate(values, target):\n    lo, hi = 0, len(values)\n    while lo < hi:\n        mid = (lo + hi) // 2\n        if values[mid] < target:\n            lo = mid + 1\n        else:\n            hi = mid\n    return lo if lo < len(values) and values[lo] == target else -1\n'},
                 ('code.python.algorithms','code.python.tests')),
        CodeCase('python.stable_unique','python','Implement unique(values): preserve first occurrence order, handle an empty input, and do not mutate the input list.',
                 {'task.py':'def unique(values):\n    return sorted(set(values))\n'},
                 'import task\nfor xs in ([],[3,1,3,2,1],[0,-1,0,-1,4]):\n original=list(xs)\n expected=[v for i,v in enumerate(xs) if v not in xs[:i]]\n assert task.unique(xs)==expected\n assert xs==original\n',
                 {'task.py':'def unique(values):\n    seen = set()\n    result = []\n    for value in values:\n        if value not in seen:\n            seen.add(value)\n            result.append(value)\n    return result\n'},
                 ('code.python.algorithms','code.python.debug')),
        CodeCase('shell.quoted_filename','shell','Repair copy.sh: copy the contents of the first pathname argument to the second, preserving bytes even when either pathname contains spaces or shell punctuation.',
                 {'copy.sh':'#!/bin/sh\ncat $1 > $2\n'},
                 'import subprocess,pathlib\np=pathlib.Path\nfor source,dest in [("source one.txt","dest two.txt"),("semi;colon.txt","literal $name.txt")]:\n raw="one\\nUnicode: \\u03b1\\n".encode()\n p(source).write_bytes(raw)\n subprocess.run(["/bin/sh","copy.sh",source,dest],check=True)\n assert p(dest).read_bytes()==raw\n',
                 {'copy.sh':'#!/bin/sh\nset -eu\ncat -- "$1" > "$2"\n'},
                 ('code.shell.quoting','tools.write')),
        CodeCase('shell.failure_status','shell','Repair check.sh: return a nonzero exit status when the input file does not contain READY; return zero when it does. The file is its first argument.',
                 {'check.sh':'#!/bin/sh\ngrep -q READY "$1"\necho checked\n'},
                 'import subprocess,pathlib\np=pathlib.Path\nfor text,success in [("READY\\n",True),("not ready\\n",False)]:\n p("input file").write_text(text)\n result=subprocess.run(["/bin/sh","check.sh","input file"],capture_output=True)\n assert (result.returncode==0)==success\n',
                 {'check.sh':'#!/bin/sh\nset -eu\ngrep -q READY "$1"\necho checked\n'},
                 ('code.shell.errors','tools.finish')),
    )

def grade(case,observations,final_files):
    if not observations or any(not r.get('settled') for r in observations):return dict(status='unavailable',reasons=['Missing settled host execution evidence'])
    last=observations[-1]
    if last.get('kind')!='host-verdict' or last.get('checker_id')!=digest(case.check_program):return dict(status='unavailable',reasons=['Missing independent host checker result'])
    if set(final_files)!=set(case.before):return dict(status='fail',reasons=['Unexpected source files'])
    passed=last.get('passed') is True
    return dict(status='pass' if passed else 'fail',reasons=[] if passed else [last.get('reason','Independent checks failed')])
