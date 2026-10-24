"""Compare completed native optimizer continuations without loading whole models.

This is a mechanics gate, not a learning or promotion decision. Both runs must
belong to the same checked practice selection and completed optimizer cursor.
"""
from pathlib import Path
import argparse
import hashlib
import json
import math
import sys


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    ensure_ascii=False).encode()).hexdigest()


def compare_arrays(left, right, *, atol, rtol):
    import numpy as np
    if left.size != right.size:
        raise ValueError('Tensor element counts differ')
    result = dict(elements=int(left.size), bitwise_differences=0,
                  outside_tolerance=0, maximum_absolute_error=0.0,
                  maximum_tolerance_ratio=0.0)
    for start in range(0, left.size, 1 << 20):
        a = np.asarray(left[start:start + (1 << 20)])
        b = np.asarray(right[start:start + (1 << 20)])
        if not np.isfinite(a).all() or not np.isfinite(b).all():
            raise ValueError('Nonfinite completed tensor')
        error = abs(a.astype('float64') - b.astype('float64'))
        bound = atol + rtol * np.maximum(abs(a.astype('float64')), abs(b.astype('float64')))
        result['bitwise_differences'] += int(np.count_nonzero(a.view('uint32') != b.view('uint32')))
        result['outside_tolerance'] += int(np.count_nonzero(error > bound))
        result['maximum_absolute_error'] = max(result['maximum_absolute_error'], float(error.max(initial=0)))
        result['maximum_tolerance_ratio'] = max(result['maximum_tolerance_ratio'], float((error / bound).max(initial=0)))
    return result


def run(args):
    import numpy as np
    sys.path.insert(0, str(args.pcc_root.resolve(strict=True)))
    from tools.pcc_native_training import read_optimizer_state, sha256
    from tools.gguf_reader import GGUFFile
    if not math.isfinite(args.atol) or not math.isfinite(args.rtol) or args.atol <= 0 or args.rtol < 0:
        raise ValueError('Finite predeclared positive absolute/nonnegative relative tolerances required')
    results = [json.loads(p.read_text()) for p in (args.left_result, args.right_result)]
    for result in results:
        if result.get('result_id') != digest({k: v for k, v in result.items() if k != 'result_id'}) or result.get('status') != 'MECHANICS_COMPLETE':
            raise ValueError('Pinned completed result required')
    if results[0]['pilot_id'] != results[1]['pilot_id']:
        raise ValueError('Different practice selections')
    candidates = [r['candidate'] for r in results]
    states = []
    for candidate in candidates:
        if sha256(candidate['candidate_path']) != candidate['candidate_sha256']:
            raise ValueError('Candidate artifact changed')
        state = read_optimizer_state(candidate['optimizer_state_path'], candidate['optimizer_state_sha256'])
        if state['model_sha256'] != candidate['candidate_sha256']:
            raise ValueError('Optimizer state belongs to different weights')
        states.append(state)
    for key in ('config', 'completed_steps', 'example_cursor', 'dataset_sha256', 'tensors'):
        if states[0][key] != states[1][key]:
            raise ValueError('Completed state differs: ' + key)
    weights = [GGUFFile(c['candidate_path']) for c in candidates]
    layouts = [[(t.name, t.shape, t.type_name) for t in w.tensors] for w in weights]
    if layouts[0] != layouts[1] or any(t.type_name != 'F32' for t in weights[0].tensors):
        raise ValueError('Identical complete F32 candidate layouts required')
    rows = []
    for left, right in zip(weights[0].tensors, weights[1].tensors):
        arrays = [np.memmap(c['candidate_path'], dtype='<f4', mode='r',
                            offset=w.data_start + t.offset, shape=(t.elements,))
                  for c, w, t in zip(candidates, weights, (left, right))]
        rows.append(dict(kind='weight', name=left.name,
                         **compare_arrays(*arrays, atol=args.atol, rtol=args.rtol)))
        del arrays
    offsets = []
    for c in candidates:
        with Path(c['optimizer_state_path']).open('rb') as stream:
            stream.seek(8)
            offsets.append(16 + int.from_bytes(stream.read(8), 'little'))
    for tensor in states[0]['tensors']:
        count = math.prod(tensor['shape'])
        if tensor['bytes'] != count * 4:
            raise ValueError('Unexpected optimizer tensor byte layout')
        arrays = [np.memmap(c['optimizer_state_path'], dtype='<f4', mode='r',
                            offset=o, shape=(count,)) for c, o in zip(candidates, offsets)]
        rows.append(dict(kind='moment', name=tensor['name'],
                         **compare_arrays(*arrays, atol=args.atol, rtol=args.rtol)))
        del arrays
        offsets = [o + tensor['bytes'] for o in offsets]
    if any(o != Path(c['optimizer_state_path']).stat().st_size for c, o in zip(candidates, offsets)):
        raise ValueError('Optimizer state has trailing or truncated data')
    output = dict(schema=1, scope='Completed actual-model optimizer continuation mechanics; no learning claim',
                  pilot_id=results[0]['pilot_id'], left_result_id=results[0]['result_id'],
                  right_result_id=results[1]['result_id'], atol=args.atol, rtol=args.rtol,
                  completed_steps=states[0]['completed_steps'], example_cursor=states[0]['example_cursor'],
                  weight_tensors=len(weights[0].tensors), moment_tensors=len(states[0]['tensors']),
                  elements=sum(r['elements'] for r in rows),
                  bitwise_differences=sum(r['bitwise_differences'] for r in rows),
                  outside_tolerance=sum(r['outside_tolerance'] for r in rows),
                  maximum_absolute_error=max(r['maximum_absolute_error'] for r in rows),
                  rows=rows, promoted=False)
    output['status'] = 'PASS' if output['outside_tolerance'] == 0 else 'FAIL'
    with args.output.open('x') as stream:
        json.dump(output, stream, indent=2)
        stream.write('\n')
    print(json.dumps({k: v for k, v in output.items() if k != 'rows'}))
    return 0 if output['status'] == 'PASS' else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pcc-root', type=Path, required=True)
    parser.add_argument('--left-result', type=Path, required=True)
    parser.add_argument('--right-result', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--atol', type=float, required=True)
    parser.add_argument('--rtol', type=float, required=True)
    raise SystemExit(run(parser.parse_args()))
