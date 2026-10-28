"""Prepare the mixed curriculum after checking known protected questions.

This is an exact-prompt guard, not a semantic leakage or mastery test. Protected
inputs and admitted lessons stay in the operator's private output directory.
"""
import argparse
import hashlib
import json
from pathlib import Path

from sss.adapters.foundation_training import build_pack
from sss.curriculum import BY_ID, exercise_for, foundation_graph
from sss_integration.foundation_screen import OLD
from sss_integration.optimizer_study_prepare import prepare


def protected_panel(path, expected_sha256, count, kind):
    raw = path.read_bytes()
    actual = hashlib.sha256(raw).hexdigest()
    if actual != expected_sha256:
        raise ValueError('Protected panel identity mismatch: ' + kind)
    data = json.loads(raw)
    if kind == 'study864':
        if not isinstance(data, dict) or data.get('split') != 'development':
            raise ValueError('Invalid development panel')
        prompts = [row['exercise']['prompt'] for row in data['cases']]
    elif kind == 'external64':
        if not isinstance(data, list):
            raise ValueError('Invalid external panel')
        prompts = [row['prompt'] for row in data]
    else:
        raise ValueError('Unknown protected panel')
    if len(prompts) != count or any(not isinstance(p, str) or not p for p in prompts):
        raise ValueError('Invalid protected panel size or prompt')
    return prompts, actual


def check_overlap(practice, panels):
    if not practice or any(not isinstance(p, str) or not p for p in practice):
        raise ValueError('Invalid practice prompts')
    seen = set(practice)
    result = {}
    for name, prompts in panels.items():
        if not prompts or any(not isinstance(p, str) or not p for p in prompts):
            raise ValueError('Invalid protected prompts: ' + name)
        collisions = len(seen.intersection(prompts))
        result[name] = dict(cases=len(prompts), distinct_prompts=len(set(prompts)),
                            exact_prompt_collisions=collisions)
        if collisions:
            raise ValueError('Protected prompt collision: ' + name)
    return result


def run(a):
    graph = foundation_graph()
    skills = [key for key in graph.order if graph.nodes[key]['status'] == 'implemented']
    if len(skills) != 66:
        raise ValueError('The 66-skill snapshot changed; requalify the curriculum')
    pack = build_pack(skills, seed=a.seed, practice_per_gate=a.practice_per_gate,
                      checks_per_gate=a.checks_per_gate, generation_profile='mixed66-v1')
    study, study_sha = protected_panel(a.study, a.study_sha256, 864, 'study864')
    external, external_sha = protected_panel(a.external, a.external_sha256, 64, 'external64')
    screen_skills = sorted(set(BY_ID) - OLD)
    if len(screen_skills) != 57:
        raise ValueError('Foundation screen definition changed')
    screen = [exercise_for(skill, 'development', i, gate='independent', seed=20261028).prompt
              for skill in screen_skills for i in range(8)]
    comparisons = check_overlap([row['prompt'] for row in pack['exercises'] if row['split'] == 'practice'],
                                dict(study864=study, external64=external, reconstructed_foundation_screen=screen))
    a.skills = skills
    a.generation_profile = 'mixed66-v1'
    summary = prepare(a)
    if summary['pack_id'] != pack['pack_id']:
        raise ValueError('Prepared pack differs from protected-prompt check')
    receipt = dict(schema=1, status='EXACT_PROMPT_CHECK_PASSED', pack_id=pack['pack_id'],
                   panels=comparisons, study_sha256=study_sha, external_sha256=external_sha,
                   semantic_disjointness_established=False,
                   scope='Known panels only; reconstructed screen uses current generator; no semantic leakage check')
    with (a.output / 'protected-prompt-check.json').open('x', encoding='utf-8') as out:
        json.dump(receipt, out, indent=2, sort_keys=True)
        out.write('\n')
    return receipt


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--pcc-root', type=Path, required=True)
    p.add_argument('--model', type=Path, required=True)
    p.add_argument('--model-contract-id', required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--study', type=Path, required=True)
    p.add_argument('--study-sha256', required=True)
    p.add_argument('--external', type=Path, required=True)
    p.add_argument('--external-sha256', required=True)
    p.add_argument('--seed', type=int, default=20261028)
    p.add_argument('--practice-per-gate', type=int, default=8)
    p.add_argument('--checks-per-gate', type=int, default=2)
    print(json.dumps(run(p.parse_args()), sort_keys=True))


if __name__ == '__main__':
    main()
