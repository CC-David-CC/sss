from dataclasses import replace
import json
from pathlib import Path
import tempfile
import unittest

from sss import reasoning
from sss.curriculum import exercise_for, foundation_graph
from sss.foundations import Exercise, check, reference
from sss.foundation_cli import example_archive
from sss.episodes import EpisodeArchive
from sss.records import digest


def problem(facts=('a', 'b')):
    return reasoning.ArgumentProblem(dict(
        atoms=['a', 'b', 'c', 'd'], facts=list(facts), query='c',
        rules=[dict(id='joint', premises=['a', 'b'], conclusion='c'),
               dict(id='alternative', premises=['d'], conclusion='c')]))


def exercise(kind, payload):
    return Exercise('test', kind, 'practice', 'fixture', 'fixture', 'independent', payload, 'fixture')


class ReasoningTests(unittest.TestCase):
    def test_joint_premises_are_and_alternate_rules_are_or(self):
        self.assertFalse(reasoning.entails(problem(['a'])))
        self.assertFalse(reasoning.check_proof(problem(['a']), ['joint']))
        self.assertTrue(reasoning.check_proof(problem(), ['joint']))
        self.assertTrue(reasoning.entails(problem(['d'])))
        self.assertTrue(reasoning.check_proof(problem(['d']), ['alternative']))
        self.assertFalse(reasoning.check_proof(problem(['d']), ['joint']))

    def test_missing_fact_is_unknown_and_converse_is_invalid(self):
        p = problem(['a'])
        self.assertTrue(reasoning.check_counterexample(p, dict(a=True, b=False, c=False, d=False)))
        self.assertFalse(reasoning.check_counterexample(p, dict(a=True, b=True, c=False, d=False)))
        self.assertFalse(reasoning.check_counterexample(p, dict(a=False, b=False, c=False, d=False)))
        self.assertFalse(reasoning.check_counterexample(p, dict(a=True, b=False, c=False)))
        self.assertFalse(reasoning.check_counterexample(p, dict(a=1, b=0, c=0, d=0)))
        converse = problem(['c']).document()
        converse['query'] = 'a'
        self.assertFalse(reasoning.entails(reasoning.ArgumentProblem(converse)))

    def test_cycles_and_fabricated_steps_cannot_bootstrap_a_proof(self):
        p = reasoning.ArgumentProblem(dict(atoms=['a', 'b'], facts=[], query='b', rules=[
            dict(id='ab', premises=['a'], conclusion='b'),
            dict(id='ba', premises=['b'], conclusion='a')]))
        self.assertFalse(reasoning.entails(p))
        for proof in (['ab', 'ba'], ['unknown'], [True], ['ab', 'ab'], {'proof': 'b'}):
            self.assertFalse(reasoning.check_proof(p, proof))

    def test_argument_is_detached_and_bounded(self):
        source = problem().document()
        frozen = reasoning.ArgumentProblem(source)
        identity = frozen.identity
        source['facts'].clear()
        returned = frozen.document()
        returned['rules'][0]['premises'].clear()
        self.assertTrue(reasoning.entails(frozen))
        self.assertEqual(identity, digest(frozen.document()))
        for mutate in (
                lambda p: p['atoms'].append('a'),
                lambda p: p.update(atoms=['p' + str(i) for i in range(11)]),
                lambda p: p['rules'][0].update(premises=[]),
                lambda p: p['rules'][0].update(premises=['unknown']),
                lambda p: p['rules'][0].update(conclusion='a')):
            value = problem().document()
            mutate(value)
            with self.assertRaises(ValueError):
                reasoning.ArgumentProblem(value)

    def test_reverse_support_accepts_alternatives_but_rejects_larger_sets(self):
        p = problem(['a'])
        e = exercise('reverse_support', dict(problem=p.document(), choices=['b', 'd']))
        for answer in (dict(assumptions=['b'], proof=['joint']),
                       dict(assumptions=['d'], proof=['alternative'])):
            self.assertTrue(check(e, json.dumps(answer)))
        for answer in (dict(assumptions=['b', 'd'], proof=['joint']),
                       dict(assumptions=['c'], proof=[]),
                       dict(assumptions=[], proof=['joint']),
                       dict(assumptions=['b', 'b'], proof=['joint'])):
            self.assertFalse(check(e, json.dumps(answer)))

    def test_premise_removal_requires_a_real_proof_or_counterexample(self):
        e = exercise('premise_removal', dict(problem=problem(['a']).document()))
        self.assertTrue(check(e, json.dumps(dict(status='not_entailed', counterexample=dict(a=True, b=False, c=False, d=False)))))
        self.assertFalse(check(e, '{"status":"not_entailed"}'))
        self.assertFalse(check(e, '{"status":"entailed","proof":["joint"]}'))
        alternate = replace(e, payload=dict(problem=problem(['a', 'd']).document()))
        self.assertTrue(check(alternate, '{"status":"entailed","proof":["alternative"]}'))
        self.assertFalse(check(alternate, '{"status":"not_entailed","counterexample":{"a":true,"b":false,"c":false,"d":true}}'))

    def test_near_twins_need_the_method_and_result(self):
        rows = [reasoning.generate('method_selection', 'practice', i, 'independent', 17) for i in range(4)]
        self.assertEqual(len({(r.payload['a'], r.payload['b']) for r in rows}), 1)
        self.assertEqual({r.payload['method'] for r in rows}, set(reasoning.METHODS))
        for row in rows:
            correct = json.loads(reference(row))
            self.assertTrue(check(row, json.dumps(correct)))
            wrong = dict(correct, method=reasoning.METHODS[(reasoning.METHODS.index(correct['method']) + 1) % 4])
            self.assertFalse(check(row, json.dumps(wrong)))
            self.assertFalse(check(row, json.dumps(dict(correct, answer='987654321'))))
        # Numeric equivalence is accepted; the exact reference spelling is not required.
        answer = json.loads(reference(rows[3]))
        n = reasoning.Fraction(answer['answer'])
        answer['answer'] = f'{n.numerator * 3}/{n.denominator * 3}'
        self.assertTrue(check(rows[3], json.dumps(answer)))

    def test_generated_references_and_transfer_judgments(self):
        seen_statuses, previous_judgments = set(), set()
        for kind in reasoning.KINDS:
            for split in ('practice', 'development', 'qualification'):
                for gate in ('independent', 'composition', 'transfer_recovery'):
                    for index in range(8):
                        row = reasoning.generate(kind, split, index, gate, 20261023)
                        answer = json.loads(reference(row))
                        with self.subTest(kind=kind, split=split, gate=gate, index=index):
                            self.assertTrue(check(row, json.dumps(answer)))
                            self.assertFalse(check(row, '{"passed":true}'))
                            if gate == 'transfer_recovery':
                                previous_judgments.add(answer['previous_correct'])
                                self.assertFalse(check(row, json.dumps(dict(answer, previous_correct=not answer['previous_correct']))))
                            base = answer['answer'] if gate == 'transfer_recovery' else answer
                            if kind == 'premise_removal':
                                seen_statuses.add(base['status'])
        self.assertEqual(seen_statuses, {'entailed', 'not_entailed'})
        self.assertEqual(previous_judgments, {True, False})

    def test_three_graph_layers_do_not_confer_mastery(self):
        graph = foundation_graph()
        self.assertIn('logic.joint_premises', graph.prerequisites('logic.reverse_support'))
        self.assertIn('logic.premise_robustness', graph.prerequisites('research.findings'))
        self.assertFalse(graph.readiness('logic.reverse_support', [])['ready'])
        e = exercise_for('logic.joint_premises', 'practice', 0)
        receipt = reasoning.practice_evidence(e, reference(e), '0' * 64)
        self.assertEqual(receipt['model_mastery'], 'unmeasured')
        self.assertFalse(receipt['weights_updated'])
        self.assertEqual(receipt['argument_id'], digest(receipt['argument']))
        protected = exercise_for('logic.joint_premises', 'development', 0)
        with self.assertRaises(ValueError):
            reasoning.practice_evidence(protected, reference(protected), '0' * 64)

    def test_existing_teaching_export_preserves_question_and_proof_receipt(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = example_archive(Path(directory) / 'lesson', 'logic.premise_robustness')
            reopened = EpisodeArchive(archive.path)
            records = reopened.records()
            receipt = json.loads((archive.path / 'reasoning-evidence.json').read_bytes())
            question = reopened.read(receipt['source_question_record_id'])
            self.assertEqual(question['kind'], 'question')
            self.assertTrue(any(row['kind'] == 'answer' and row['verified'] for row in records))
            self.assertFalse(any(row['kind'] == 'thinking' for row in records))
            self.assertEqual(receipt['evidence_id'], digest({k: v for k, v in receipt.items() if k != 'evidence_id'}))


    def test_delayed_revisit_uses_causal_note_and_original_archive(self):
        from sss.episodes import verify_note
        with tempfile.TemporaryDirectory() as directory:
            archive = example_archive(Path(directory) / 'day', 'logic.joint_premises', delayed_revisit=True)
            note = json.loads((archive.path / 'revisit-note.json').read_bytes())
            receipt = json.loads((archive.path / 'revisit-evidence.json').read_bytes())
            self.assertTrue(verify_note(archive, note))
            original = archive.read(receipt['retrieved_question_record_id'], through=note['as_of'])
            followup = archive.read(receipt['source_question_record_id'])
            self.assertLess(original['seq'], note['as_of'])
            self.assertGreater(followup['seq'], note['as_of'])
            self.assertNotIn(original['id'], [e['record_id'] for e in note['entries']])
            reread = next(r for r in archive.records() if r['topic'] == 'archive-reread')
            self.assertEqual(reread['text'], original['text'])
            self.assertEqual(len([r for r in archive.records() if r['question_id'].startswith('math-')]), 4)
            self.assertEqual(archive.records()[-1]['resolves'], 'evening-revisit')
            self.assertFalse(receipt['model_inference'])
            self.assertEqual(receipt['evidence_id'], digest({k:v for k,v in receipt.items() if k != 'evidence_id'}))


if __name__ == '__main__':
    unittest.main()
