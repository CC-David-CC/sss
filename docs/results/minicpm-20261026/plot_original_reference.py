"""Shared presentation references from the published original-model receipts.

The original sweep used a different runtime. Never fill in an unmeasured F32
point or present these historical scores as a matched-runtime causal estimate.
"""
import csv
import json
from pathlib import Path


def original_scores(root):
    root = Path(root)
    with (root/'original-quantization.csv').open(newline='', encoding='utf8') as f:
        rows = list(csv.DictReader(f))
    proof = json.loads((root/'original-quantization-validation.json').read_text(encoding='utf8'))
    assert proof['status'] == 'PASS' and proof['unique_complete_cases_per_format'] == 864
    assert len(rows) == len({r['format'] for r in rows}) == 7
    assert {r['evaluation_id'] for r in rows} == {proof['common_evaluation_id']}
    assert {r['runtime_id'] for r in rows} == {proof['common_runtime_id']}
    assert all(int(r['cases']) == 864 for r in rows)
    return {r['format']: r for r in rows}


def add_original_curve(axis, root, formats, metric, *, horizontal=False):
    rows = original_scores(root)
    # Missing original F32 remains absent; the curve starts at measured F16.
    x = [i for i, fmt in enumerate(formats) if fmt in rows]
    y = [int(rows[formats[i]][metric]) for i in x]
    axis.plot(x, y, 'd--', color='#d06b1f', lw=1.8, markersize=5,
              label='Original model at each quant (prior runtime)')
    if horizontal:
        value = int(rows['F16'][metric])
        axis.axhline(value, color='#777777', ls=':', lw=1.2,
                     label=f'Original F16 reference: {value}/864')
    return rows
