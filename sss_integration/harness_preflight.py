"""CPU-tokenize captured client requests with the actual PCC model formatter.

This reads an inspected model/profile; it performs no inference or allocation.
The declared model limit is a planning bound, not hardware qualification.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(*, pcc_root, profile_path, requests, model_limit, output_bound, output):
    if type(model_limit) is not int or model_limit < 2 or not 1 <= output_bound < model_limit:
        raise ValueError('Explicit positive context and output bounds required')
    output = Path(output)
    if output.exists():
        raise FileExistsError('Inspect the original preflight; use a new identity for changed inputs')
    pcc = Path(pcc_root).resolve(strict=True)
    sys.path[:0] = [str(pcc), str(pcc/'experimental/branching_context/src')]
    from serve.cow_http import model_text_components
    from serve.cow_compat import Frontend
    profile = json.loads(Path(profile_path).read_bytes())
    original_capacity = profile['execution']['capacity']
    profile = copy.deepcopy(profile)
    profile['execution']['capacity'] = model_limit
    components = model_text_components(profile['model_path'], {'enable_thinking': True},
        model_contract_id=profile['model_contract_id'], mixed_inputs=True)
    rows = []; hashes = {}
    for client, path in sorted(requests.items()):
        hashes[client] = sha(path)
        captured = json.loads(Path(path).read_bytes())
        if type(captured) is not list or not captured:
            raise ValueError('Nonempty original request lists required')
        for index, request in enumerate(captured):
            body = copy.deepcopy(request['body'])
            if request['path'] not in ('/v1/responses', '/v1/chat/completions'):
                raise ValueError('Unsupported captured API route')
            dialect = 'responses' if request['path'].endswith('/responses') else 'chat'
            preparer = Frontend(object(), components['render'].__self__, profile, body['model'], output_bound, thinking=False)
            try:
                plan = preparer.prepare(body, dialect)
            except ValueError as error:
                rows.append(dict(client=client, request=index, dialect=dialect,
                    status='REFUSED', error_type=type(error).__name__, error=str(error)))
                continue
            tokens, bound = len(plan['full']), plan['bound']
            rows.append(dict(client=client, request=index, dialect=dialect, status='PREPARED', prompt_tokens=tokens,
                output_reserve=bound, fits_original_profile=tokens+bound <= original_capacity,
                minimum_power_two_capacity=2**((tokens+bound-1).bit_length()),
                effective_settings=plan['settings'], request_seed=plan['seed']))
    if not rows:
        raise ValueError('At least one captured request required')
    result = dict(schema=1, preflight_sha256=sha(__file__), source_pcc=subprocess.check_output(['git','-C',str(pcc),'rev-parse','HEAD'],text=True).strip(),
        protocol_source_sha256={name:sha(pcc/name) for name in ('serve/cow_http.py','serve/cow_compat.py','serve/frontend.py','serve/responses.py')},
        profile_sha256=sha(profile_path), model_contract_id=profile['model_contract_id'], captured_request_sha256=hashes,
        declared_model_limit=model_limit, original_profile_capacity=original_capacity,
        thinking=False, model_inference=False, gpu_allocated=False, hardware_capacity_qualified=False,
        results=rows, limits=[
            'Tokenization of captured requests only; no model quality, GPU capacity or throughput claim.',
            'Captured fixture trajectories are not predictions of live model trajectory length.',
            'Weights, actual backend sampling and runtime containment need separate qualification.'])
    with output.open('x') as stream:
        json.dump(result, stream, indent=2); stream.write('\n')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pcc-root', required=True)
    parser.add_argument('--profile', required=True)
    parser.add_argument('--requests', required=True, help='Private JSON mapping client name to captured request file')
    parser.add_argument('--model-limit', type=int, required=True)
    parser.add_argument('--output-bound', type=int, default=512)
    parser.add_argument('--output', required=True, help='New aggregate JSON file')
    args = parser.parse_args()
    result = run(pcc_root=args.pcc_root, profile_path=args.profile,
        requests=json.loads(Path(args.requests).read_bytes()), model_limit=args.model_limit,
        output_bound=args.output_bound, output=args.output)
    ready = [r for r in result['results'] if r['status'] == 'PREPARED']
    print(json.dumps(dict(requests=len(result['results']), prepared=len(ready), refused=len(result['results'])-len(ready),
        minimum_power_two_capacity=max((r['minimum_power_two_capacity'] for r in ready), default=None),
        all_fit_original_profile=all(r.get('fits_original_profile', False) for r in result['results']), model_inference=False)))
    return 0 if len(ready) == len(result['results']) else 1


if __name__ == '__main__':
    raise SystemExit(main())
