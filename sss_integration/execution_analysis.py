"""Analyze completed evaluation artifacts with bounded independent CPU workers."""
import argparse
import json
from pathlib import Path
from sss.studies.execution_analysis import analyze_assessments


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assessment', action='append', required=True, help='LABEL=/absolute/assessment/directory')
    parser.add_argument('--workers', type=int, default=4)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    inputs = {}
    for value in args.assessment:
        label, path = value.split('=', 1)
        if label in inputs: raise ValueError('Duplicate assessment label')
        inputs[label] = str(Path(path).resolve(strict=True))
    result = analyze_assessments(inputs, workers=args.workers)
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2); stream.write('\n')
    print(json.dumps(dict(report_id=result['report_id'], assessments=len(result['assessments']), **result['analysis'])))


if __name__ == '__main__': main()
