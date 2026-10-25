"""Export aggregate precision evidence from completed native matrix evaluations.

Does not run inference or training. Reads completed original/trained summaries
and their corresponding frozen results; private answer text is not exported.
"""
import argparse
import json
from pathlib import Path
from sss.records import digest, file_sha256
from sss.studies.quantization import quantization_report


def collect(directory, formats):
    directory = Path(directory)
    rows = []
    sources = {}
    unavailable = {}
    for family in ('original', 'trained'):
        for fmt in formats:
            name = family+'-'+fmt
            summary_path = directory/(name+'-summary.json')
            if not summary_path.exists():
                continue
            summary = json.loads(summary_path.read_text())
            sources[summary_path.name] = file_sha256(summary_path)
            if summary.get('family') != family or summary.get('format') != fmt:
                raise ValueError('Summary variant identity differs: '+name)
            if summary.get('status') != 'COMPLETE':
                unavailable[family, fmt] = summary.get('status')
                continue  # Failed/missing evaluations never become zero model scores.
            result_path = directory/name/'result.json'
            result = json.loads(result_path.read_text())
            if (summary.get('family') != family or summary.get('format') != fmt
                    or any(summary.get(k) != result.get(k) for k in
                           ('status', 'model_sha256', 'cases', 'passed', 'finished', 'evaluation_id', 'runtime_id'))):
                raise ValueError('Summary differs from original frozen result: '+name)
            rows.append(dict(family=family, format=fmt, bytes=summary['bytes'], result=result))
            sources[name+'/result.json'] = file_sha256(result_path)
    report = quantization_report(rows, formats)
    report.pop('report_id')
    for row in report['rows']:
        key = row['family'], row['format']
        if key in unavailable:
            row.update(status='INFRASTRUCTURE_INCOMPLETE', source_status=unavailable[key])
    if unavailable:
        report['status'] = 'INCOMPLETE'
    report['source_sha256'] = sources
    report['implementation_sha256'] = dict(adapter=file_sha256(__file__),
        study=file_sha256(Path(__file__).parents[1]/'sss/studies/quantization.py'))
    report['report_id'] = digest(report)
    return report


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--directory', type=Path, required=True)
    p.add_argument('--formats', nargs='+', required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    report = collect(a.directory, a.formats)
    with a.output.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps(dict(status=report['status'], measured=report['measured_variants'],
                          expected=report['expected_variants'], report_id=report['report_id'])))
