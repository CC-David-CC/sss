"""Parallel offline geometry reports using PCC's checked saved-matrix reader.

Inputs are existing PCC matrix subsets. No model serving, training or GPU calls.
"""
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
import argparse, hashlib, importlib.util, json, multiprocessing, os, re, time


def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def reader(source, expected):
    path=Path(source)/'experimental/native_training/matrix_geometry.py'
    if sha(path)!=expected:raise ValueError('PCC diagnostic implementation changed')
    spec=importlib.util.spec_from_file_location('pcc_saved_matrix_geometry',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def measure(source, expected, baseline, candidate, output, threads):
    os.environ.update(OPENBLAS_NUM_THREADS=str(threads),OMP_NUM_THREADS=str(threads),
                      MKL_NUM_THREADS=str(threads),CUDA_VISIBLE_DEVICES='')
    result=reader(source,expected).measure(candidate['subset'],baseline,output)
    reader(source,expected)
    return result


def run(pcc_root,manifest_path,output,*,workers=4,blas_threads=2):
    if (type(workers) is not int or not 1<=workers<=64 or type(blas_threads) is not int or not 1<=blas_threads<=64):
        raise ValueError('Explicit bounded CPU worker and BLAS thread counts required')
    started=time.monotonic();source=Path(pcc_root).resolve(strict=True)
    manifest_path=Path(manifest_path).resolve(strict=True);original=manifest_path.read_bytes()
    plan=json.loads(original)
    if (type(plan) is not dict or set(plan)!={'schema','baseline_subset','candidates','behavior_file','update'}
            or type(plan['schema']) is not int or plan['schema']!=1
            or type(plan['update']) is not int or plan['update']<1
            or type(plan['candidates']) is not list or not 1<=len(plan['candidates'])<=64):
        raise ValueError('Closed matrix-subset and matched-update manifest required')
    candidates=[];labels=set()
    for candidate in plan['candidates']:
        if (type(candidate) is not dict or set(candidate)!={'label','subset'}
                or type(candidate['label']) is not str or not re.fullmatch('[A-Za-z][A-Za-z0-9_-]{0,63}',candidate['label'])
                or candidate['label']=='original' or candidate['label'] in labels):
            raise ValueError('Unique candidate labels and local subsets required')
        labels.add(candidate['label'])
        candidates.append(dict(label=candidate['label'],subset=str(Path(candidate['subset']).resolve(strict=True))))
    baseline=Path(plan['baseline_subset']).resolve(strict=True)
    root=Path(output).absolute()
    if any(root.resolve().is_relative_to(path) for path in [baseline,*[Path(c['subset']) for c in candidates]]):
        raise ValueError('Keep new reports outside immutable input subsets')
    implementation=sha(source/'experimental/native_training/matrix_geometry.py')
    diag=reader(source,implementation);base=diag.read_subset(baseline)
    names=[row['name'] for row in base['matrices']]
    behavior_path=Path(plan['behavior_file']).resolve(strict=True);behavior_bytes=behavior_path.read_bytes()
    scores=json.loads(behavior_bytes)
    if scores.get('status')!='PARTIAL_CURVE' or scores['baseline']['model_sha256']!=base['model_sha256']:
        raise ValueError('Matching frozen development evidence and original weights required')
    frozen={'original':base}
    for candidate in candidates:
        subset=diag.read_subset(candidate['subset'])
        points=[point for point in scores['points'] if point['arm']==candidate['label'] and point['update']==plan['update']]
        if (len(points)!=1 or points[0]['model_sha256']!=subset['model_sha256']
                or [(row['name'],row['shape']) for row in subset['matrices']]!=[(row['name'],row['shape']) for row in base['matrices']]):
            raise ValueError('Saved matrix identities must match the selected scored checkpoint before analysis')
        frozen[candidate['label']]=subset
    root.mkdir(mode=0o700,parents=True,exist_ok=False);(root/'jobs').mkdir(mode=0o700)
    (root/'input-manifest-private.json').write_bytes(original)
    jobs=[dict(label='original',subset=str(baseline)),*candidates];complete={};errors=[]
    count=min(workers,len(jobs))
    with ProcessPoolExecutor(max_workers=count,mp_context=multiprocessing.get_context('spawn')) as pool:
        pending={pool.submit(measure,str(source),implementation,str(baseline),job,str(root/'jobs'/(job['label']+'.json')),blas_threads):job for job in jobs}
        for future in as_completed(pending):
            label=pending[future]['label']
            try:complete[label]=future.result()
            except Exception as exc:errors.append(dict(label=label,type=type(exc).__name__,detail=str(exc)))
    rows=[];models=[];matched=[]
    for label,result in complete.items():
        try:
            if (result['status']!='COMPLETE' or result['weights_updated'] is not False or result['promoted'] is not False
                    or result['baseline_model_sha256']!=base['model_sha256']
                    or result['baseline_subset_id']!=base['subset_id']
                    or result['subset_id']!=frozen[label]['subset_id']
                    or [row['name'] for row in result['matrices']]!=names):
                raise ValueError('Matching completed PCC matrix measurements required')
            update=0 if label=='original' else plan['update']
            if label!='original':
                selected=[point for point in scores['points'] if point['arm']==label and point['update']==update]
                if len(selected)!=1 or selected[0]['model_sha256']!=result['model_sha256']:
                    raise ValueError('Saved matrices differ from the selected scored checkpoint')
                point=selected[0]
                matched.append({key:point[key] for key in ['arm','update','presentations','passed','finished','answer_gains','answer_losses','model_sha256','evaluation_evidence_sha256']})
            models.append(dict(arm=label,update=update,model_sha256=result['model_sha256']))
            rows.extend(dict(arm=label,update=update,matrix_name=row['name'],weights=row['weights'],
                change_from_base=row['change_from_base'],model_sha256=result['model_sha256'],
                baseline_model_sha256=result['baseline_model_sha256'],subset_id=result['subset_id'],
                baseline_subset_id=result['baseline_subset_id']) for row in result['matrices'])
        except Exception as exc:errors.append(dict(label=label,type=type(exc).__name__,detail=str(exc)))
    if (manifest_path.read_bytes()!=original or behavior_path.read_bytes()!=behavior_bytes
            or diag.read_subset(baseline)!=base):raise ValueError('Frozen geometry inputs changed')
    if any(diag.read_subset(candidate['subset'])!=frozen[candidate['label']] for candidate in candidates):
        raise ValueError('Frozen candidate subsets changed')
    reader(source,implementation)
    value=dict(schema=1,kind='sss.optimizer-geometry-block.v1',status='COMPLETE' if len(models)==len(jobs) and not errors else 'PARTIAL',
        scope='PCC full float64 SVD of selected saved matrices and accumulated changes, joined to existing behavior evidence',
        update=plan['update'],matrix_names=names,models=sorted(models,key=lambda row:row['arm']),
        results=sorted(rows,key=lambda row:(row['arm'],row['matrix_name'])),behavior=sorted(matched,key=lambda row:row['arm']),
        behavior_evaluation_id=scores['evaluation_id'],behavior_runtime_id=scores['runtime_id'],
        input_manifest_sha256=hashlib.sha256(original).hexdigest(),behavior_file_sha256=hashlib.sha256(behavior_bytes).hexdigest(),
        pcc_implementation_sha256=implementation,report_implementation_sha256=sha(__file__),
        source_evidence_sha256={label:sha(root/'jobs'/(label+'.json')) for label in complete},
        cpu_workers=count,blas_threads_per_worker=blas_threads,elapsed_wall_seconds=time.monotonic()-started,
        errors=errors,gpu_used=False,weights_updated=False,promoted=False)
    with (root/'result.json').open('x') as stream:json.dump(value,stream,indent=2,allow_nan=False);stream.write('\n')
    return value


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ['pcc-root','manifest','output']:parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--workers',type=int,default=4);parser.add_argument('--blas-threads',type=int,default=2)
    args=parser.parse_args(argv)
    value=run(args.pcc_root,args.manifest,args.output,workers=args.workers,blas_threads=args.blas_threads)
    print(json.dumps(dict(status=value['status'],matrix_measurements=len(value['results']),errors=len(value['errors']),gpu_used=False)))
    return 0 if value['status']=='COMPLETE' else 2


if __name__=='__main__':raise SystemExit(main())
