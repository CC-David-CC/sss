"""Shared presentation references from the published original-model receipts.

The original sweep used a different runtime. Include only verified measured
points; these historical scores are not a matched-runtime causal estimate.
"""
import csv
import hashlib
import json
from pathlib import Path


def original_scores(root):
    root = Path(root)
    with (root/'original-quantization.csv').open(newline='', encoding='utf8') as f:
        rows = list(csv.DictReader(f))
    proof = json.loads((root/'original-quantization-validation.json').read_text(encoding='utf8'))
    assert proof['status'] == 'PASS' and proof['unique_complete_cases_per_format'] == 864
    assert len(rows) == len({r['format'] for r in rows}) == 8
    assert {r['format'] for r in rows} == {'F32','F16','Q8_0','Q5_K_M','Q4_K_M','Q3_K_M','Q2_K','Q1_0'}
    receipt = root / proof['additional_f32_verification']['receipt']
    assert hashlib.sha256(receipt.read_bytes()).hexdigest() == proof['additional_f32_verification']['sha256']
    f32 = json.loads(receipt.read_text())
    assert f32['status'] == 'PASS' and f32['case_receipts'] == 864
    row = next(r for r in rows if r['format'] == 'F32')
    assert int(row['passed']) == f32['correct'] and int(row['finished']) == f32['finished']
    assert row['model_sha256'] == f32['model_sha256']
    paired_path = root / proof['additional_f32_verification']['paired_receipt']
    assert hashlib.sha256(paired_path.read_bytes()).hexdigest() == proof['additional_f32_verification']['paired_receipt_sha256']
    paired = json.loads(paired_path.read_text())
    assert paired['status'] == 'PASS' and paired['same_runtime_as_original_f16']
    assert paired['model_sha256'] == f32['model_sha256']
    assert paired['source_receipts_sha256'] == f32['source_receipts_sha256']
    assert all(value == 0 for value in paired['paired_vs_original_f16'].values())
    assert {r['evaluation_id'] for r in rows} == {proof['common_evaluation_id']}
    assert {r['runtime_id'] for r in rows} == {proof['common_runtime_id']}
    assert all(int(r['cases']) == 864 for r in rows)
    return {r['format']: r for r in rows}


def add_original_curve(axis, root, formats, metric, *, horizontal=False):
    rows = original_scores(root)
    # F32 is backed by the separately audited, already existing 864-case run.
    x = [i for i, fmt in enumerate(formats) if fmt in rows]
    y = [int(rows[formats[i]][metric]) for i in x]
    axis.plot(x, y, 'd--', color='#d06b1f', lw=1.8, markersize=5,
              label='Original model at each quant (prior runtime)')
    if horizontal:
        value = int(rows['F16'][metric])
        axis.axhline(value, color='#777777', ls=':', lw=1.2,
                     label=f'Original F16 reference: {value}/864')
    return rows
