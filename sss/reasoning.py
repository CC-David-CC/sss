"""Original bounded reasoning exercises, inspired by LearnHarness's teaching ideas.

Skill prerequisites, arguments inside an exercise, and measured mastery are
separate records. These positive Horn rules are explicit exercise assumptions,
not inferred natural-language truths. No model runtime or training authority.
"""
from copy import deepcopy
from fractions import Fraction
from itertools import combinations
from pathlib import Path
import hashlib
import json
import random

from .graph import identifier
from .records import canonical, digest

KINDS = ('joint_premises', 'premise_removal', 'reverse_support', 'method_selection')
METHODS = ('add', 'subtract', 'multiply', 'divide')
CHECKER = 'bounded-reasoning-v1'


class ArgumentProblem:
    """Detached, bounded problem. Several rules may justify the same conclusion.

    Cycles are allowed as hypotheses, but never establish facts on their own.
    All rule premises are jointly required. Facts omitted from the problem are
    unknown, not false. Complete truth assignments provide counterexamples.
    """
    def __init__(self, document):
        if type(document) is not dict or set(document) != {'atoms', 'facts', 'rules', 'query'}:
            raise ValueError('Expected an explicit bounded argument problem')
        value = deepcopy(document)
        atoms = value['atoms']
        if type(atoms) is not list or not 1 <= len(atoms) <= 10:
            raise ValueError('Expected 1..10 atoms')
        for atom in atoms:
            identifier(atom)
        if len(atoms) != len(set(atoms)):
            raise ValueError('Duplicate atom')
        facts = value['facts']
        if (type(facts) is not list or any(type(x) is not str for x in facts)
                or len(facts) != len(set(facts)) or not set(facts) <= set(atoms)):
            raise ValueError('Invalid fixed facts')
        if type(value['query']) is not str or value['query'] not in atoms:
            raise ValueError('Unknown query')
        rules = value['rules']
        if type(rules) is not list or not 1 <= len(rules) <= 32:
            raise ValueError('Expected 1..32 rules')
        ids = set()
        for rule in rules:
            if type(rule) is not dict or set(rule) != {'id', 'premises', 'conclusion'}:
                raise ValueError('Invalid rule')
            key = identifier(rule['id'])
            if key in ids:
                raise ValueError('Duplicate rule identity')
            ids.add(key)
            premises = rule['premises']
            if (type(premises) is not list or not premises
                    or any(type(x) is not str for x in premises)
                    or len(premises) != len(set(premises))
                    or not set(premises) <= set(atoms)):
                raise ValueError('Invalid joint premises')
            if type(rule['conclusion']) is not str or rule['conclusion'] not in atoms:
                raise ValueError('Unknown conclusion')
            if rule['conclusion'] in premises:
                raise ValueError('Direct self-justification is not a useful rule')
        self._encoded = canonical(value)
        self.identity = hashlib.sha256(self._encoded).hexdigest()

    def document(self):
        return json.loads(self._encoded)

    def with_facts(self, facts):
        value = self.document()
        value['facts'] = list(facts)
        return ArgumentProblem(value)


def _forward(problem):
    """Reference constructor: least fixed point plus a valid rule sequence."""
    p = problem.document()
    known = set(p['facts'])
    steps = []
    if p['query'] in known:
        return known, steps
    while True:
        changed = False
        for rule in p['rules']:
            if rule['conclusion'] not in known and set(rule['premises']) <= known:
                known.add(rule['conclusion'])
                steps.append(rule['id'])
                changed = True
                if p['query'] in known:
                    return known, steps
        if not changed:
            return known, steps


def _truth_models(problem):
    """Independent semantic oracle: enumerate assignments, never forward-chain."""
    p = problem.document()
    for bits in range(1 << len(p['atoms'])):
        assignment = {atom: bool(bits & (1 << i)) for i, atom in enumerate(p['atoms'])}
        if (all(assignment[f] for f in p['facts'])
                and all(not all(assignment[a] for a in rule['premises'])
                        or assignment[rule['conclusion']] for rule in p['rules'])):
            yield assignment


def entails(problem):
    query = problem.document()['query']
    return all(model[query] for model in _truth_models(problem))


def check_proof(problem, proof):
    """Replay only justified steps; a cycle without a starting fact cannot pass."""
    p = problem.document()
    if type(proof) is not list or len(proof) > len(p['rules']):
        return False
    if any(type(key) is not str for key in proof) or len(proof) != len(set(proof)):
        return False
    rules = {rule['id']: rule for rule in p['rules']}
    known = set(p['facts'])
    for key in proof:
        if key not in rules or not set(rules[key]['premises']) <= known:
            return False
        known.add(rules[key]['conclusion'])
    return p['query'] in known


def check_counterexample(problem, assignment):
    p = problem.document()
    if type(assignment) is not dict or set(assignment) != set(p['atoms']):
        return False
    if any(type(value) is not bool for value in assignment.values()):
        return False
    return (not assignment[p['query']] and all(assignment[f] for f in p['facts'])
            and all(not all(assignment[a] for a in rule['premises'])
                    or assignment[rule['conclusion']] for rule in p['rules']))


def _supports(problem, choices, size):
    facts = problem.document()['facts']
    return (problem.with_facts(facts + list(extra)) for extra in combinations(choices, size))


def _check_answer(kind, payload, answer):
    if type(answer) is not dict:
        return False
    if kind == 'method_selection':
        if set(answer) != {'method', 'answer'} or answer['method'] != payload['method']:
            return False
        from .foundations import number
        value = (number(answer['answer']) - payload['offset']) / payload['scale']
        a, b = payload['a'], payload['b']
        # Denominator-cleared equations, independently of the reference arithmetic.
        if answer['method'] == 'add':
            return value - a == b
        if answer['method'] == 'subtract':
            return a - value == b
        if answer['method'] == 'multiply':
            return value / b == a
        return value * b == a
    problem = ArgumentProblem(payload['problem'])
    if kind == 'joint_premises':
        return (set(answer) == {'proof'} and check_proof(problem, answer['proof'])
                and entails(problem))
    if kind == 'premise_removal':
        if answer.get('status') == 'entailed':
            return (set(answer) == {'status', 'proof'} and entails(problem)
                    and check_proof(problem, answer['proof']))
        return (set(answer) == {'status', 'counterexample'}
                and answer['status'] == 'not_entailed'
                and check_counterexample(problem, answer['counterexample']))
    if kind == 'reverse_support':
        if set(answer) != {'assumptions', 'proof'}:
            return False
        selected = answer['assumptions']
        choices = payload['choices']
        if (type(selected) is not list or any(type(x) is not str for x in selected)
                or len(selected) != len(set(selected)) or not set(selected) <= set(choices)):
            return False
        candidate = problem.with_facts(problem.document()['facts'] + selected)
        if not check_proof(candidate, answer['proof']) or not entails(candidate):
            return False
        # Accept ANY smallest support, rather than matching one reference proof.
        return not any(entails(p) for n in range(len(selected)) for p in _supports(problem, choices, n))
    return False


def check(exercise, completion):
    try:
        if type(completion) is not str or len(completion.encode()) > 65536:
            return False
        answer = json.loads(completion)
        if exercise.gate == 'transfer_recovery':
            if (type(answer) is not dict or set(answer) != {'previous_correct', 'answer'}
                    or type(answer['previous_correct']) is not bool):
                return False
            previous = _check_answer(exercise.kind, exercise.payload, exercise.payload['previous'])
            return (answer['previous_correct'] == previous
                    and _check_answer(exercise.kind, exercise.payload, answer['answer']))
        return _check_answer(exercise.kind, exercise.payload, answer)
    except (ValueError, TypeError, KeyError, IndexError, ZeroDivisionError, OverflowError, RecursionError):
        return False


def _reference_answer(kind, payload):
    if kind == 'method_selection':
        a, b = Fraction(payload['a']), Fraction(payload['b'])
        value = {'add': lambda: a + b, 'subtract': lambda: a - b,
                 'multiply': lambda: a * b, 'divide': lambda: a / b}[payload['method']]()
        return dict(method=payload['method'], answer=str(value * payload['scale'] + payload['offset']))
    problem = ArgumentProblem(payload['problem'])
    p = problem.document()
    if kind == 'reverse_support':
        for size in range(len(payload['choices']) + 1):
            for extra in combinations(payload['choices'], size):
                known, proof = _forward(problem.with_facts(p['facts'] + list(extra)))
                if p['query'] in known:
                    return dict(assumptions=list(extra), proof=proof)
        raise ValueError('No support exists in the supplied choices')
    known, proof = _forward(problem)
    if kind == 'joint_premises':
        if p['query'] not in known:
            raise ValueError('No proof exists')
        return dict(proof=proof)
    if p['query'] in known:
        return dict(status='entailed', proof=proof)
    return dict(status='not_entailed', counterexample={atom: atom in known for atom in p['atoms']})


def reference(exercise):
    answer = _reference_answer(exercise.kind, exercise.payload)
    if exercise.gate == 'transfer_recovery':
        previous = exercise.payload['previous']
        # Constructive reference is separate from the exhaustive grading oracle.
        # Generated suggestions are either this exact valid construction or an
        # explicitly invalid method/empty proof, not arbitrary user suggestions.
        correct = previous == answer
        answer = dict(previous_correct=correct, answer=answer)
    return json.dumps(answer, sort_keys=True)


def generate(kind, split, index, gate, seed):
    from .foundations import Exercise
    if (kind not in KINDS or split not in ('practice', 'development', 'qualification')
            or type(index) is not int or index < 0 or type(seed) is not int
            or gate not in ('independent', 'composition', 'transfer_recovery')):
        raise ValueError('Invalid bounded reasoning coordinates')
    family = f'{split}-{gate}-{kind}-v1'
    # Four method-selection neighbors share numbers, but require different methods.
    coordinate = index // 4 if kind == 'method_selection' else index
    rng = random.Random(int(hashlib.sha256(f'{seed}:{family}:{coordinate}'.encode()).hexdigest(), 16))
    if kind == 'method_selection':
        low, high = {'practice': (2, 19), 'development': (21, 79), 'qualification': (101, 499)}[split]
        a, b = rng.randint(low, high), rng.randint(low, high)
        if a < b:
            a, b = b, a
        method = METHODS[index % 4]
        payload = dict(a=a, b=b, method=method, scale=3 if gate == 'composition' else 1,
                       offset=-2 if gate == 'composition' else 0)
        variants = {
            'practice': (f'You have {a} tiles and receive {b} more. How many tiles now?',
                         f'You have {a} tiles and give away {b}. How many remain?',
                         f'There are {a} packets with {b} tiles in each. How many tiles total?',
                         f'Share {a} tiles equally among {b} packets. How many tiles per packet? Fractions are allowed.'),
            'development': (f'A store has {a} bolts; a delivery adds {b}. Find the new stock.',
                            f'From a stock of {a} bolts, {b} are sold. Find the remaining stock.',
                            f'A store receives {a} cartons, each holding {b} bolts. Find the total delivered.',
                            f'A length of {a} metres is split into {b} equal sections. Find one section length.'),
            'qualification': (f'A tank holds {a} litres before {b} litres are poured in. Find its resulting contents.',
                              f'A tank initially holds {a} litres; {b} litres are drained. Find what is left.',
                              f'Each of {a} tanks holds {b} litres. Find their combined contents.',
                              f'{a} litres are distributed evenly among {b} tanks. Find one tank\'s share.')}
        prompt = variants[split][index % 4]
        if gate == 'composition':
            prompt += ' Multiply that result by 3, then subtract 2.'
        prompt += ' Return JSON {"method": "add|subtract|multiply|divide", "answer": "exact number"}. Choose the method for the original problem; answer is the final result.'
    else:
        atoms = [f'p{v}' for v in rng.sample(range(100000, 999999), 8)]
        a, b, c, d, e, f, g, h = atoms
        rule_ids = [f'r{v}' for v in rng.sample(range(10000, 99999), 5)]
        rules = [dict(id=rule_ids[0], premises=[a, b], conclusion=c),
                 dict(id=rule_ids[1], premises=[c], conclusion=d),
                 dict(id=rule_ids[2], premises=[d, e], conclusion=f),
                 dict(id=rule_ids[3], premises=[f], conclusion=h),
                 dict(id=rule_ids[4], premises=[g], conclusion=c)]
        rng.shuffle(rules)
        query = c if gate == 'independent' else h if gate == 'composition' else f
        facts = [a, b, e]
        if index % 3 == 1:
            facts.append(g)
        elif index % 3 == 2 and kind == 'joint_premises':
            facts = [g, e]
        payload = {}
        if kind == 'premise_removal':
            removed = b if index % 2 == 0 else e
            payload.update(original_facts=list(facts), removed=removed)
            facts = [v for v in facts if v != removed]
        elif kind == 'reverse_support':
            facts = [a, e] if index % 3 == 0 else [e]
            payload['choices'] = ([b, g] if index % 3 == 0 else [a, b] if index % 3 == 1 else [a, b, g])
            rng.shuffle(payload['choices'])
        shuffled_atoms = list(atoms)
        rng.shuffle(shuffled_atoms)
        payload['problem'] = ArgumentProblem(dict(atoms=shuffled_atoms, facts=facts, rules=rules, query=query)).document()
        prompt = ('These are assumptions of a bounded logic exercise. Every premise of one rule is required together; '
                  'different rules provide alternative routes. A rule cannot be run backwards. '
                  'An absent fact is unknown, not false. Problem: ' + json.dumps(payload['problem'], sort_keys=True) + '. ')
        if kind == 'joint_premises':
            prompt += 'Prove the query. Return JSON {"proof": [rule IDs in a valid execution order]}; cite only rules whose premises are already established.'
        elif kind == 'premise_removal':
            prompt += (f'The earlier facts were {json.dumps(payload["original_facts"])}. Fact {payload["removed"]} has been withdrawn; '
                       'the problem above already contains only the remaining facts. Does the query still follow? '
                       'Return {"status":"entailed","proof":[rule IDs]} or {"status":"not_entailed","counterexample":{every atom: true or false}}. '
                       'A counterexample must satisfy every remaining fact and rule while making the query false.')
        else:
            prompt += ('Choose the smallest NUMBER of extra assumptions from ' + json.dumps(payload['choices'])
                       + ' that makes the query follow. Different smallest sets are acceptable. '
                       'Return {"assumptions":[chosen atom IDs],"proof":[rule IDs in a valid execution order]}.')
    if gate == 'transfer_recovery':
        previous = _reference_answer(kind, payload)
        if index % 3 != 0:
            if kind == 'method_selection':
                previous['method'] = METHODS[(index + 1) % 4]
            elif kind == 'premise_removal':
                previous = dict(status='entailed', proof=[])
            elif kind == 'reverse_support':
                previous = dict(assumptions=[], proof=[])
            else:
                previous = dict(proof=[])
        payload['previous'] = previous
        prompt += (' An earlier worker proposed ' + json.dumps(previous, sort_keys=True)
                   + '. Check it independently. Return {"previous_correct":true or false,"answer":the corrected original JSON response}.')
    return Exercise('foundation.' + kind, kind, split, family,
                    f'{seed}:{family}:{index}', gate, payload, prompt)


def practice_evidence(exercise, answer, question_record_id):
    """Source-linked result; a checked exercise is not a model mastery result."""
    if exercise.split != 'practice' or not check(exercise, answer):
        raise ValueError('Only independently checked practice may be exported')
    if (type(question_record_id) is not str or len(question_record_id) != 64
            or any(c not in '0123456789abcdef' for c in question_record_id)):
        raise ValueError('Exact archive question identity required')
    value = dict(schema=1, relation='argument_under_explicit_assumptions',
                 exercise_id=exercise.identity, skill_id=exercise.skill_id,
                 source_question_record_id=question_record_id,
                 checker=CHECKER, checker_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                 answer_sha256=hashlib.sha256(answer.encode()).hexdigest(),
                 passed=True, model_mastery='unmeasured', model_inference=False,
                 weights_updated=False, trained=False)
    if 'problem' in exercise.payload:
        problem = ArgumentProblem(exercise.payload['problem'])
        value.update(argument_id=problem.identity, argument=problem.document())
    else:
        value['relation'] = 'method_and_numeric_result'
    value['evidence_id'] = digest(value)
    return value
