"""Prepare checked mixed practice and separate protected cases; no model updates."""
from pathlib import Path
import argparse
import hashlib
import json
import sys


def prepare(a):
    pcc = a.pcc_root.resolve(strict=True)
    sys.path[:0] = [str(pcc), str(pcc / 'experimental/branching_context/src')]
    from serve.cow_http import model_text_components
    from serve.server import Service
    from tools.gguf_reader import GGUFFile
    from tools.pcc_lessons import LessonService
    from sss.records import digest, file_sha256, canonical
    from sss.adapters.foundation_training import build_pack, validate_pack, initialize, SYSTEM
    from sss.adapters.pcc_foundation_render import PCCFoundationRenderer
    from sss.foundations import reference
    root = a.output.resolve()
    root.mkdir(mode=0o700, parents=True, exist_ok=False)
    pack = build_pack(a.skills, seed=a.seed, practice_per_gate=a.practice_per_gate,
                      checks_per_gate=a.checks_per_gate, generation_profile=a.generation_profile)
    exercises = validate_pack(pack)
    components = model_text_components(a.model, dict(enable_thinking=False), model_contract_id=a.model_contract_id)
    tokenizer = components['tokenizer']
    renderer = PCCFoundationRenderer(components)
    metadata = GGUFFile(a.model).metadata
    tokenizer_id = digest(dict(metadata={k:v for k,v in metadata.items() if k.startswith('tokenizer.')},
                               source_sha256=file_sha256(pcc / 'tools/strata_tokenizer.py')))
    def no_training(*args):
        raise RuntimeError('Preparation grants no model update authority')
    sequence_profile = ('dense-llama-action-8k-v1' if a.generation_profile == 'mixed66-v1'
                        else 'dense-llama-short-v1')
    token_limit = 8192 if a.generation_profile == 'mixed66-v1' else 512
    service = LessonService(root / 'lesson-service', a.model_contract_id,
        lambda text:tokenizer.encode(text, parse_special=False), no_training,
        max_tokens=token_limit, max_steps=1000, sequence_profile=sequence_profile,
        rendered_tokenize=lambda text:tokenizer.encode(text, parse_special=True))
    def write(path, value):
        with path.open('xb') as stream:
            stream.write(canonical(value) + b'\n')
    try:
        tree = initialize(service, pack, renderer, renderer_sha256=renderer.renderer_sha256,
                          tokenizer_sha256=tokenizer_id, target_policy='actions_answer')
        records = [service.lesson(r['lesson_id']) for r in service.lessons()['lessons']]
        by_verification = {}
        for row in records:
            key = row['lesson']['evidence']['verification_sha256']
            if key in by_verification:
                raise ValueError('Practice is not uniquely bound to its admitted lesson')
            by_verification[key] = row
        exercise_rows = {digest(row):row for row in pack['exercises']}
        selected = []; selection = []; protected = dict(development=[], qualification=[])
        for exercise in exercises:
            if exercise.split == 'practice':
                answer = reference(exercise)
                verification = digest(dict(exercise_id=exercise.identity, checker_id=pack['implementation_id'], answer=answer, passed=True))
                row = by_verification[verification]
                selected.append(row['example'])
                selection.append(dict(exercise_id=exercise.identity, lesson_id=row['lesson_id'],
                    skill_id=exercise.skill_id, gate=exercise.gate, selected_targets=sum(row['example']['loss_mask']),
                    consumed_tokens=len(row['example']['tokens']), verification_sha256=verification))
            else:
                messages = [dict(role='system', content=SYSTEM), dict(role='user', content=exercise.prompt)]
                tokens = Service.encode_prompt(renderer.encoder, messages, None,
                    dict(enable_thinking=False, add_generation_prompt=True))
                protected[exercise.split].append(dict(exercise_id=exercise.identity,
                    prefix_tokens=tokens, exercise=exercise_rows[exercise.identity]))
        purpose = ('mixed_66_curriculum_practice' if a.generation_profile == 'mixed66-v1'
                   else 'fixed_compute_optimizer_study_practice')
        practice = dict(schema=1, purpose=purpose,
            origin='owned synthetic checked demonstrations; not observed model failures',
            model_contract_id=a.model_contract_id, model_sha256=file_sha256(a.model),
            pack_id=pack['pack_id'], tree_id=tree.identity, renderer_sha256=renderer.renderer_sha256,
            tokenizer_sha256=tokenizer_id, target_policy='actions_answer', examples=selected,
            selection=selection, protected_cases_exported=False, promoted=False)
        practice['practice_id'] = digest(practice)
        write(root / 'training-practice-private.json', practice)
        for split, cases in protected.items():
            value = dict(schema=1, split=split, pack_id=pack['pack_id'],
                         model_contract_id=a.model_contract_id, renderer_sha256=renderer.renderer_sha256,
                         tokenizer_sha256=tokenizer_id, cases=cases)
            value['evaluation_id'] = digest(value)
            write(root / (split + '-private.json'), value)
        write(root / 'pack-private.json', pack)
        summary = dict(schema=1, status='PREPARED_NO_MODEL_RUN', pack_id=pack['pack_id'],
            practice_id=practice['practice_id'], skills=pack['skills'], practice_examples=len(selected),
            unique_practice_questions=len(selected)-pack['repeated_practice_questions'],
            repeated_practice_occurrences=pack['repeated_practice_questions'],
            development_cases=len(protected['development']), qualification_cases=len(protected['qualification']),
            maximum_training_input_tokens=max(len(e['tokens']) for e in selected),
            maximum_selected_targets=max(sum(e['loss_mask']) for e in selected),
            maximum_evaluation_prefix_tokens=max(len(c['prefix_tokens']) for rows in protected.values() for c in rows),
            model_sha256=practice['model_sha256'], tokenizer_sha256=tokenizer_id,
            renderer_sha256=renderer.renderer_sha256, weights_updated=False, promoted=False)
        if a.generation_profile == 'mixed66-v1':
            summary.update(generation_profile=a.generation_profile,
                sequence_profile=sequence_profile, token_limit=token_limit,
                finite_boolean_truth_inputs_shared_across_splits=pack['finite_boolean_truth_inputs_shared_across_splits'],
                semantic_disjointness_established=pack['semantic_disjointness_established'])
        write(root / 'preparation-result.json', summary)
        print(json.dumps(summary), flush=True)
        return summary
    finally:
        service.close()


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--pcc-root', type=Path, required=True)
    p.add_argument('--model', type=Path, required=True)
    p.add_argument('--model-contract-id', required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--skills', nargs='+', required=True)
    p.add_argument('--seed', type=int, required=True)
    p.add_argument('--practice-per-gate', type=int, default=32)
    p.add_argument('--checks-per-gate', type=int, default=32)
    p.add_argument('--generation-profile', choices=['without-replacement-v1'], default='without-replacement-v1')
    prepare(p.parse_args())
