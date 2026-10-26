"""Optional BW artifact correction -> fixed S3 oracle -> exact PCC lesson export.

Owner registration is a separate decision. There is no model tool, scheduler,
native inference, training or dynamic checker import in this module.
"""
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import stat

from sss.records import canonical, digest, file_sha256
from sss.practice_oracle import AffineClampFoldCase, FAMILY, strict_json, grade_observation
from sss.episodes import EpisodeArchive, training_tokens, export_text, render_text
from sss.profiles import TARGET_POLICIES
from sss.adapters.episode_lessons import pcc_lesson
from sss.adapters.bw_practice_oracle import observe, implementation_pins, validate_source, DRIVER

SHA = re.compile('[a-f0-9]{64}\\Z')
REPRESENTATION = 'final-artifact-v1'
MAX_FILE = 4 * 1024**2
MAX_EXPORT = 300 * 1024**2
SYSTEM = 'Return only the requested final-artifact-v1 JSON object. Preserve the exact source text and its final newline. Do not add commentary or tool calls.'
TASK = ('Repair task.py. Define exactly one unannotated function '
        'solve(values, scale, offset, low, high). For each integer in values, '
        'multiply by scale, add offset, and clamp the result inclusively between low and high. '
        'Return a dictionary with exactly two entries: values is the transformed list in its '
        'original order, and total is the sum of that transformed list. Handle empty input, '
        'negative values and negative scale; do not mutate any input. low is at most high. '
        'Use one pure function with exactly these five positional arguments: no defaults, '
        'annotations, decorators, imports, classes, nested functions, lambdas, global or nonlocal '
        'state, async operations, yields, context managers, or underscore-prefixed names. '
        'Use local variables and ordinary expressions/control flow; callable names are limited '
        'to solve, len, range, enumerate, sum, min, max, abs, sorted, set, list, dict, tuple, int '
        'and bool. Do not rebind any Python builtin or solve. Attribute access is limited to '
        'append, add, get, items, keys, values, count, index and pop. Do not use annotated '
        'assignments or match statements. Keep the source within 32 KiB and its parsed syntax '
        'tree within 2,048 nodes. '
        'Keep task.py as the only project file, preserve its basic mode, run an appropriate '
        'check and explicitly finish after checking the saved file.')


class PracticeExportRefused(ValueError):
    """Unavailable, invalid or ineligible evidence; never a fabricated lesson."""


def _hash(raw): return hashlib.sha256(raw).hexdigest()


def _hex(value):
    if type(value) is not str or not SHA.fullmatch(value): raise PracticeExportRefused('explicit SHA-256 owner pin required')
    return value


def _json(value): return json.loads(canonical(value))


def _read(path, maximum=MAX_FILE):
    from branchwrite.lesson_capture import _read as read_private
    return read_private(path, maximum)


def _write(path, value):
    raw = value if type(value) is bytes else canonical(value)
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(raw); stream.flush(); os.fchmod(stream.fileno(), 0o400); os.fsync(stream.fileno())


def _sources():
    import sss.records as records
    import sss.episodes as episodes
    import sss.profiles as profiles
    import sss.lesson_targets as lesson_targets
    import sss.adapters.episode_lessons as lessons
    import tools.pcc_lesson_segments as pcc_segments
    return dict(adapter=file_sha256(__file__), records=file_sha256(records.__file__), episodes=file_sha256(episodes.__file__),
                profiles=file_sha256(profiles.__file__), lesson_targets=file_sha256(lesson_targets.__file__), episode_lessons=file_sha256(lessons.__file__),
                pcc_lesson_segments=file_sha256(pcc_segments.__file__),oracle=implementation_pins())


@dataclass(frozen=True)
class BWArtifactPractice:
    case: AffineClampFoldCase
    model_contract_id: str
    baseline_source_sha256: str
    source_mode: int = 0o644
    split_role: str = 'practice'
    protected_case_ids: tuple = ()
    protected_texts: tuple = ()
    protected_source_sha256s: tuple = ()

    def __post_init__(self):
        if type(self.case) is not AffineClampFoldCase: raise PracticeExportRefused('fixed installed affine case required')
        self.case.__post_init__(); _hex(self.model_contract_id); _hex(self.baseline_source_sha256)
        if self.split_role != 'practice' or type(self.source_mode) is not int or self.source_mode not in (0o600, 0o644):
            raise PracticeExportRefused('owned practice scope and supported non-executable source mode required')
        for values in (self.protected_case_ids, self.protected_texts, self.protected_source_sha256s):
            if type(values) is not tuple or len(values) > 4096 or any(type(v) is not str or not v for v in values):
                raise PracticeExportRefused('immutable bounded owner protection descriptors required')
        if sum(len(t.encode()) for t in self.protected_texts) > 4*1024**2:
            raise PracticeExportRefused('owner protection descriptor exceeds bound')
        if self.case.case_id in self.protected_case_ids or self.case.split_id in self.protected_case_ids:
            raise PracticeExportRefused('protected case or split cannot be practice')
        for value in self.protected_source_sha256s: _hex(value)

    @property
    def task_prompt(self): return TASK

    def descriptor(self):
        """Private owner configuration, not a model request or public artifact."""
        self.__post_init__()
        return dict(schema=1, kind='bw-artifact-practice-v1',
            case=dict(family=self.case.family, case_id=self.case.case_id, split_id=self.case.split_id, rows=self.case.rows),
            model_contract_id=self.model_contract_id, baseline_source_sha256=self.baseline_source_sha256,
            source_mode=self.source_mode, split_role=self.split_role,
            protection=dict(case_ids=list(self.protected_case_ids), texts=list(self.protected_texts),
                            source_sha256s=list(self.protected_source_sha256s)))

    @classmethod
    def from_descriptor(cls, value):
        keys={'schema','kind','case','model_contract_id','baseline_source_sha256','source_mode','split_role','protection'}
        if type(value) is not dict or set(value)!=keys or type(value['schema']) is not int or value['schema']!=1 or value['kind']!='bw-artifact-practice-v1':
            raise PracticeExportRefused('closed owner practice descriptor required')
        c=value['case'];p=value['protection']
        if type(c) is not dict or set(c)!={'family','case_id','split_id','rows'} or c['family']!=FAMILY or type(p) is not dict or set(p)!={'case_ids','texts','source_sha256s'}:
            raise PracticeExportRefused('closed fixed-family case/protection descriptor required')
        if any(type(p[k]) is not list for k in p): raise PracticeExportRefused('owner protection arrays required')
        return cls(AffineClampFoldCase.install(c['case_id'],c['split_id'],c['rows']),value['model_contract_id'],
            value['baseline_source_sha256'],value['source_mode'],value['split_role'],tuple(p['case_ids']),tuple(p['texts']),tuple(p['source_sha256s']))

    def binding(self):
        return dict(schema=1, kind='bw-artifact-practice-v1', descriptor_sha256=digest(self.descriptor()),
            case=self.case.pins, model_contract_id=self.model_contract_id,
            baseline_source_sha256=self.baseline_source_sha256, source_mode=self.source_mode,
            split_role=self.split_role, task_prompt_sha256=_hash(self.task_prompt.encode()),
            protection_sha256=digest(self.descriptor()['protection']))


def _artifact(source, mode):
    if type(source) is not bytes or not 0 < len(source) <= 32768: raise PracticeExportRefused('bounded exact task.py bytes required')
    text=source.decode('utf8',errors='strict')
    return canonical(dict(path='task.py',mode=mode,source=text)).decode('utf8')


def _extract(text, mode):
    value = strict_json(text)
    if (type(value) is not dict or set(value)!={'path','mode','source'} or value['path']!='task.py'
            or type(value['mode']) is not int or value['mode']!=mode or type(value['source']) is not str
            or canonical(value).decode()!=text): raise PracticeExportRefused('noncanonical final-artifact representation')
    return value['source'].encode('utf8',errors='strict')


class PCCArtifactRenderer:
    """Actual owner PCC template/tokenizer, metadata and tokenization only."""
    @staticmethod
    def tokenizer_identity(components):
        from serve.cow_renderer import renderer_identity_receipt
        encoder=components['render'].__self__
        receipt=renderer_identity_receipt(components['tokenizer'],encoder.template.source,encoder.template_kwargs,
            model_contract_id='metadata-only-tokenizer-identity',
            **(dict(tool_binding=encoder.tool_binding) if getattr(encoder,'tool_binding',None) is not None else {}))
        return digest(receipt['tokenizer'])

    def __init__(self, components, *, model_contract_id, tokenizer_sha256, maximum_tokens, stop_token_ids):
        from serve.cow_prompt_encoder import CowPromptEncoder
        from serve.cow_renderer import renderer_identity_receipt
        self.encoder=components['render'].__self__;self.tokenizer=components['tokenizer']
        if not isinstance(self.encoder,CowPromptEncoder): raise PracticeExportRefused('actual PCC prompt encoder required')
        _hex(model_contract_id);_hex(tokenizer_sha256)
        if (type(maximum_tokens) is not int or not 2<=maximum_tokens<=131072 or type(stop_token_ids) not in (tuple,list)
                or not stop_token_ids or any(type(v) is not int or v<0 for v in stop_token_ids)
                or list(stop_token_ids)!=sorted(set(stop_token_ids))): raise PracticeExportRefused('bounded model context and exact stop IDs required')
        self.model=model_contract_id;self.maximum=maximum_tokens;self.stops=tuple(stop_token_ids)
        self.tokenizer_id=tokenizer_sha256
        self._receipt=renderer_identity_receipt(self.tokenizer,self.encoder.template.source,self.encoder.template_kwargs,
            model_contract_id=model_contract_id,
            **(dict(tool_binding=self.encoder.tool_binding) if getattr(self.encoder,'tool_binding',None) is not None else {}))
        if digest(self._receipt['tokenizer'])!=tokenizer_sha256: raise PracticeExportRefused('owner tokenizer pin differs from actual tokenizer')
        owner=components.get('renderer_id')
        if owner is not None and owner!=digest(self._receipt): raise PracticeExportRefused('owner renderer differs from actual PCC identity')
        self._binding=canonical(dict(schema=1,kind='pcc-final-artifact-through-eos-renderer-v1',model_contract_id=self.model,
            renderer_sha256=digest(self._receipt),tokenizer_sha256=self.tokenizer_id,maximum_tokens=self.maximum,
            stop_token_ids=list(self.stops),representation=REPRESENTATION,
            adapter_sha256=file_sha256(__file__),system_sha256=_hash(SYSTEM.encode())))

    def binding(self): return strict_json(self._binding)

    def verify(self):
        from serve.cow_renderer import renderer_identity_receipt
        receipt=renderer_identity_receipt(self.tokenizer,self.encoder.template.source,self.encoder.template_kwargs,
            model_contract_id=self.model,
            **(dict(tool_binding=self.encoder.tool_binding) if getattr(self.encoder,'tool_binding',None) is not None else {}))
        bound=self.binding()
        if (receipt!=self._receipt or file_sha256(__file__)!=bound['adapter_sha256']
                or self.model!=bound['model_contract_id'] or self.tokenizer_id!=bound['tokenizer_sha256']
                or self.maximum!=bound['maximum_tokens'] or list(self.stops)!=bound['stop_token_ids']):
            raise PracticeExportRefused('actual renderer/helper inputs changed')

    def render(self, question, completion, *, target_policy):
        from serve.server import Service
        from tools.pcc_lesson_segments import tokenize_segments
        if target_policy not in TARGET_POLICIES: raise PracticeExportRefused('unsupported target policy')
        self.verify()
        special=getattr(self.tokenizer,'special_tokens',())
        if any(s and s in text for s in special for text in (SYSTEM,question,completion)):
            raise PracticeExportRefused('literal model controls require a separately qualified representation')
        messages=[dict(role='system',content=SYSTEM),dict(role='user',content=question)]
        prefix=self.encoder.render_prompt(messages,None,dict(enable_thinking=False,add_generation_prompt=True))
        complete_messages=messages+[dict(role='assistant',content=completion)]
        complete=self.encoder.render_prompt(complete_messages,None,dict(enable_thinking=False,add_generation_prompt=False))
        prefix_ids=Service.encode_prompt(self.encoder,messages,None,dict(enable_thinking=False,add_generation_prompt=True))
        full_ids=Service.encode_prompt(self.encoder,complete_messages,None,dict(enable_thinking=False,add_generation_prompt=False))
        if (not complete.startswith(prefix+completion) or full_ids[:len(prefix_ids)]!=prefix_ids
                or self.tokenizer.encode(prefix,parse_special=True)!=prefix_ids
                or self.tokenizer.encode(complete,parse_special=True)!=full_ids):
            raise PracticeExportRefused('actual rendering changes artifact bytes or token boundaries')
        tail=full_ids[len(prefix_ids):];eos=[i for i,t in enumerate(tail) if t in self.stops]
        if len(eos)!=1 or self.tokenizer.decode(tail[:eos[0]])!=completion:
            raise PracticeExportRefused('artifact body and one native EOS are not exact')
        # Preserve the complete actual template while ending supervision at the
        # native stop. Subsequent template whitespace is context, never a target.
        suffix=self.tokenizer.decode(tail[eos[0]+1:])
        if suffix.strip(): raise PracticeExportRefused('unexpected post-EOS template content')
        answer=self.tokenizer.decode(tail[:eos[0]+1])
        if prefix+answer+suffix!=complete: raise PracticeExportRefused('native-output/frame split changes actual template bytes')
        segments=[dict(role='user',kind='question',rendered=prefix,verified=False,scope='practice'),
                  dict(role='assistant',kind='answer',rendered=answer,verified=True,scope='practice')]
        if suffix:segments.append(dict(role='assistant',kind='framing',rendered=suffix,verified=False,scope='practice'))
        tokens=training_tokens(segments,tokenize=lambda text:self.tokenizer.encode(text,parse_special=True),
            policy=target_policy,maximum=self.maximum)
        skeleton=dict(schema=2,title='Verified BW artifact',model_contract_id=self.model,segments=segments,
            target_policy=target_policy,scope='owned-training',evidence=dict(method='sss-verified-episode-v1',
                archive_sha256='0'*64,verification_sha256='0'*64,renderer_sha256=self.binding()['renderer_sha256'],tokenizer_sha256=self.tokenizer_id))
        native=tokenize_segments(skeleton,lambda text:self.tokenizer.encode(text,parse_special=True),self.maximum)
        if any(native[k]!=tokens[k] for k in ('tokens','targets','loss_mask')):
            raise PracticeExportRefused('S3/PCC target token or mask contract differs')
        if [t for t,selected in zip(tokens['targets'],tokens['loss_mask']) if selected]!=tail[:eos[0]+1]:
            raise PracticeExportRefused('selected training targets differ from artifact through native EOS')
        return segments,tokens,dict(completion_sha256=_hash(completion.encode()),eos_token_id=tail[eos[0]],
            template_tail_sha256=_hash(suffix.encode()),post_eos_template_whitespace=suffix,
            complete_render_sha256=_hash(complete.encode()),post_eos_framing_always_masked=True,no_thinking_targets=True)


def _captures(owner, correction, correction_id, failure_id):
    from branchwrite.lesson_capture import read_capture
    from branchwrite.records import RuntimeLog,Artifact,decode
    from branchwrite.kernel import FrameKernel
    from branchwrite.project_baseline import load,parse_reference,BINDING
    owner.__post_init__();_hex(correction_id);_hex(failure_id)
    corrected=read_capture(correction,expected_capture_id=correction_id)
    failed=read_capture(corrected.directory/'failure',expected_capture_id=failure_id)
    if corrected.manifest['kind']!='correction' or corrected.failure_capture_id!=failure_id or failed.manifest['kind']!='failure':
        raise PracticeExportRefused('exact prior failure/correction captures required')
    sources=[]
    for capture in (failed,corrected):
        m=capture.manifest;files=m['files']
        if (m['model_contract_id']!=owner.model_contract_id or m['launch']['config']['bindings'].get('task')!={'type':'Text','value':owner.task_prompt}
                or len(files)!=1 or files[0]['path']!='task.py' or files[0]['mode']!=owner.source_mode or m['directories']):
            raise PracticeExportRefused('captured task/model/path/mode differs from owner practice contract')
        with RuntimeLog(capture.directory/'ledger',read_only=True) as log:
            root=FrameKernel(log).frame('program');bindings=decode(log.read_artifact(Artifact(*root['inputs'])))['bindings']
            baseline=load(log,parse_reference(bindings[BINDING][1]))
        if (set(baseline['files'])!={'task.py'} or baseline['directories']
                or baseline['files']['task.py']['sha256']!=owner.baseline_source_sha256
                or baseline['files']['task.py']['mode']!=owner.source_mode):
            raise PracticeExportRefused('captured original artifact does not match owner baseline')
        raw=capture.file_bytes('task.py');raw.decode('utf8',errors='strict')
        if _hash(raw) in owner.protected_source_sha256s: raise PracticeExportRefused('protected artifact cannot enter practice')
        sources.append(raw)
    if failed.manifest['evidence']['task_id']!=corrected.manifest['evidence']['task_id']:
        raise PracticeExportRefused('failure/correction case contracts differ')
    return failed,corrected,*sources


def _question(owner, failed_source):
    return (owner.task_prompt+'\n\nFor this teaching example, return only canonical final-artifact-v1 JSON '
        'with exactly path="task.py", mode='+str(owner.source_mode)+' and source containing the complete corrected UTF-8 file. '
        'Preserve its final newline. No Markdown fences or explanation.\n\nCaptured failed artifact:\n'+_artifact(failed_source,owner.source_mode))


def _separation(owner, renderer, question, completion, failed_source, corrected_source):
    for text in owner.protected_texts:
        if any(text in candidate for candidate in (SYSTEM,question,completion,failed_source.decode(),corrected_source.decode())):
            raise PracticeExportRefused('protected material cannot enter practice context or targets')
    full=renderer.tokenizer.encode(SYSTEM+'\n'+question+'\n'+completion,parse_special=False)
    for text in owner.protected_texts:
        ids=renderer.tokenizer.encode(text,parse_special=False)
        if ids and any(full[i:i+len(ids)]==ids for i in range(len(full)-len(ids)+1)):
            raise PracticeExportRefused('protected token material cannot enter practice')


def _oracle(case, source, directory, expected_status):
    result=strict_json(_read(directory/'result-private.json'))
    if (type(result) is not dict or type(result.get('schema')) is not int or result.get('schema')!=1
            or result.get('kind')!='sss.verified-practice-oracle.v1'
            or result.get('evidence_sha256')!=digest({k:v for k,v in result.items() if k!='evidence_sha256'})
            or any(result.get(k)!=v for k,v in dict(case.pins,**implementation_pins()).items())
            or result.get('source_sha256')!=_hash(source) or result.get('lesson_approved') is not False):
        raise PracticeExportRefused('original oracle source/case/implementation evidence differs')
    if result.get('status')=='unavailable':raise PracticeExportRefused('independent oracle was unavailable, not a failure/pass contrast')
    supported=validate_source(source,_hash(source))
    if not supported:
        if result.get('execution_attempted') is not False or result.get('status')!='fail' or 'observation' in result:
            raise PracticeExportRefused('unsupported source gate was not an original settled refusal')
    else:
        import branchwrite
        impl=digest({p.name:file_sha256(p) for p in sorted(Path(branchwrite.__file__).parent.glob('*.py'))})
        if (result.get('execution_attempted') is not True or result.get('bw_implementation_sha256')!=impl
                or result.get('bw_implementation_after_sha256')!=impl):
            raise PracticeExportRefused('actual oracle BW source closure differs')
        observation=result.get('observation',{});out=_read(directory/'stdout.bin');err=_read(directory/'stderr.bin')
        expected=dict(stdout=out.decode('utf8',errors='strict'),stderr=err.decode('utf8',errors='replace'),
            stdout_sha256=_hash(out),stderr_sha256=_hash(err),source_before_sha256=_hash(source),
            source_after_sha256=_hash(source),original_after_sha256=_hash(source))
        if any(observation.get(k)!=v for k,v in expected.items()): raise PracticeExportRefused('saved oracle bytes/source observations conflict')
        details=observation.get('details',{})
        argv=['/usr/bin/python3','-I','-B','-c',DRIVER,case.inputs_json.decode()]
        if (result.get('operation_id')!='sss-practice-oracle' or details.get('command')!='practice-oracle'
                or details.get('argv')!=argv or observation.get('isolation')!=details.get('isolation')):
            raise PracticeExportRefused('actual fixed oracle command/input/retirement differs')
        inputs=details.get('inputs')
        if (type(inputs) is not list or len(inputs)!=1 or inputs[0].get('path')!='task.py'
                or inputs[0].get('sha256')!=_hash(source) or inputs[0].get('bytes')!=len(source)):
            raise PracticeExportRefused('actual projected execution source differs')
        if _read(directory/'source/task.py')!=source or _read(directory/'world/workspace/task.py')!=source:
            raise PracticeExportRefused('original oracle execution files changed')
        grade=grade_observation(case,observation)
        if result.get('status')!=grade['status'] or grade['status']=='unavailable':
            raise PracticeExportRefused('saved oracle grade does not match independent recomputation')
    if result.get('status')!=expected_status: raise PracticeExportRefused('required failed/corrected independent contrast is absent')
    return result


def _inventory(directory):
    from branchwrite.lesson_capture import _real_path
    _real_path(directory)
    rows=[];total=0
    for p in sorted(directory.rglob('*')):
        info=p.lstat();mode=stat.S_IMODE(info.st_mode)
        relative=p.relative_to(directory).as_posix()
        if stat.S_ISDIR(info.st_mode):
            rows.append(dict(path=relative,kind='directory',mode=mode))
        elif stat.S_ISREG(info.st_mode):
            raw=_read(p);total+=len(raw)
            if total>MAX_EXPORT: raise PracticeExportRefused('export exceeds bound')
            rows.append(dict(path=relative,kind='file',mode=mode,sha256=_hash(raw),bytes=len(raw)))
        else: raise PracticeExportRefused('linked or special export entry')
    return rows


def _copy_capture(capture, output):
    from branchwrite.lesson_capture import _real_path,read_capture
    output.mkdir(mode=0o700)
    for path in sorted(capture.directory.rglob('*')):
        target=output/path.relative_to(capture.directory)
        if path.is_symlink(): raise PracticeExportRefused('linked capture source')
        if path.is_dir():_real_path(path);target.mkdir(mode=0o700)
        else:_write(target,_read(path))
    read_capture(output,expected_capture_id=capture.capture_id)


@dataclass(frozen=True)
class VerifiedBWExport:
    directory: Path
    _data: bytes
    @property
    def export_id(self): return strict_json(self._data)['export_id']
    @property
    def lesson(self): return _json(strict_json(self._data)['lesson'])
    @property
    def lesson_id(self): return digest(self.lesson)
    @property
    def tokens(self): return _json(strict_json(self._data)['tokens'])
    @property
    def proof(self): return _json(strict_json(self._data)['proof'])
    def binding(self):
        value=strict_json(self._data)
        return dict(schema=1,kind='sss.bw-verified-practice-export.v1',export_id=self.export_id,lesson_id=self.lesson_id,
            owner=value['owner'],renderer=value['renderer'],failure_capture_id=value['failure_capture_id'],
            correction_capture_id=value['correction_capture_id'],representation=REPRESENTATION,
            proof_sha256=digest(value['proof']),owner_registered=False,training_approved=False)


def export_correction(owner, correction_capture, *, correction_capture_id, failure_capture_id, renderer, output, target_policy='actions_answer'):
    if type(owner) is not BWArtifactPractice or type(renderer) is not PCCArtifactRenderer: raise PracticeExportRefused('installed owner and actual renderer required')
    if target_policy not in TARGET_POLICIES: raise PracticeExportRefused('unsupported target policy')
    failed,corrected,bad,good=_captures(owner,correction_capture,correction_capture_id,failure_capture_id)
    if renderer.model!=owner.model_contract_id: raise PracticeExportRefused('renderer model differs from practice')
    completion=_artifact(good,owner.source_mode);question=_question(owner,bad)
    if _extract(completion,owner.source_mode)!=good: raise PracticeExportRefused('artifact extraction changed checked bytes')
    _separation(owner,renderer,question,completion,bad,good)
    segments,tokens,render_proof=renderer.render(question,completion,target_policy=target_policy)
    root=Path(os.path.abspath(output))
    if root.exists() or root.is_symlink(): raise PracticeExportRefused('export output must be fresh')
    from branchwrite.lesson_capture import _real_path
    parent=_real_path(root.parent)
    if root.is_relative_to(corrected.directory) or corrected.directory.is_relative_to(root): raise PracticeExportRefused('export overlaps capture')
    root.mkdir(mode=0o700);_copy_capture(corrected,root/'capture')
    observe(owner.case,bad,_hash(bad),root/'failed-oracle');observe(owner.case,good,_hash(good),root/'corrected-oracle')
    left=_oracle(owner.case,bad,root/'failed-oracle','fail');right=_oracle(owner.case,good,root/'corrected-oracle','pass')
    archive=EpisodeArchive(root/'episode',create=True,metadata=dict(origin='independently-checked-bw-artifact-practice',
        owner_binding_sha256=digest(owner.binding()),representation=REPRESENTATION))
    archive.append('user','question',question,scope='practice')
    archive.append('assistant','answer',completion,verified=True,scope='practice')
    finished=root/'finished-training-examples';finished.mkdir(mode=0o700)
    export_text(archive,finished/'example.txt',public=False)
    proof=dict(schema=1,kind='sss.bw-artifact-proof.v1',owner_binding_sha256=digest(owner.binding()),
        failure_oracle_evidence_sha256=left['evidence_sha256'],correction_oracle_evidence_sha256=right['evidence_sha256'],
        failed_source_sha256=_hash(bad),corrected_source_sha256=_hash(good),path='task.py',mode=owner.source_mode,
        episode_head=archive.head,render=render_proof,sources=_sources(),representation=REPRESENTATION,
        exact_artifact_independently_checked=True,owner_registered=False,training_approved=False,weights_updated=False)
    lesson=pcc_lesson('Verified BW affine artifact repair',owner.model_contract_id,segments,archive_sha256=archive.head,
        verification_sha256=digest(proof),renderer_sha256=renderer.binding()['renderer_sha256'],tokenizer_sha256=renderer.tokenizer_id,
        skill_id='code.python.affine_clamp_fold',target_policy=target_policy)
    record=dict(schema=1,kind='sss.bw-verified-practice-export.v1',owner=owner.binding(),renderer=renderer.binding(),
        failure_capture_id=failure_capture_id,correction_capture_id=correction_capture_id,target_policy=target_policy,
        proof=proof,lesson=lesson,tokens=tokens,files=_inventory(root),owner_registered=False,training_approved=False)
    record['export_id']=digest(record);_write(root/'export-private.json',record)
    return read_export(root,owner=owner,expected_export_id=record['export_id'],correction_capture_id=correction_capture_id,
        failure_capture_id=failure_capture_id,renderer=renderer)


def read_export(directory, *, owner, expected_export_id, correction_capture_id, failure_capture_id, renderer):
    """Revalidate exact artifacts, original oracle observations and taught tokens; no execution."""
    if type(owner) is not BWArtifactPractice or type(renderer) is not PCCArtifactRenderer: raise PracticeExportRefused('installed owner and actual renderer required')
    _hex(expected_export_id);root=Path(directory).absolute();record=strict_json(_read(root/'export-private.json'))
    keys={'schema','kind','owner','renderer','failure_capture_id','correction_capture_id','target_policy',
          'proof','lesson','tokens','files','owner_registered','training_approved','export_id'}
    if (type(record) is not dict or set(record)!=keys or type(record.get('schema')) is not int
            or record.get('schema')!=1 or record.get('kind')!='sss.bw-verified-practice-export.v1'
            or record.get('export_id')!=expected_export_id or expected_export_id!=digest({k:v for k,v in record.items() if k!='export_id'})
            or record.get('owner')!=owner.binding() or record.get('renderer')!=renderer.binding()
            or record.get('failure_capture_id')!=failure_capture_id or record.get('correction_capture_id')!=correction_capture_id
            or record.get('owner_registered') is not False or record.get('training_approved') is not False):
        raise PracticeExportRefused('export differs from exact owner approval inputs')
    actual=[row for row in _inventory(root) if row['path']!='export-private.json']
    if actual!=record.get('files'): raise PracticeExportRefused('original export files changed or are incomplete')
    failed,corrected,bad,good=_captures(owner,root/'capture',correction_capture_id,failure_capture_id)
    left=_oracle(owner.case,bad,root/'failed-oracle','fail');right=_oracle(owner.case,good,root/'corrected-oracle','pass')
    completion=_artifact(good,owner.source_mode);question=_question(owner,bad);_separation(owner,renderer,question,completion,bad,good)
    segments,tokens,render_proof=renderer.render(question,completion,target_policy=record['target_policy'])
    archive=EpisodeArchive(root/'episode');events=archive.records()
    if (len(events)!=2 or [(e['role'],e['kind'],e['text'],e['verified'],e['scope']) for e in events]
            !=[('user','question',question,False,'practice'),('assistant','answer',completion,True,'practice')]):
        raise PracticeExportRefused('archived exact teaching content/roles differ')
    if _read(root/'finished-training-examples/example.txt')!=render_text(archive,public=False):
        raise PracticeExportRefused('saved human-readable completed example differs from exact archive')
    proof=dict(schema=1,kind='sss.bw-artifact-proof.v1',owner_binding_sha256=digest(owner.binding()),
        failure_oracle_evidence_sha256=left['evidence_sha256'],correction_oracle_evidence_sha256=right['evidence_sha256'],
        failed_source_sha256=_hash(bad),corrected_source_sha256=_hash(good),path='task.py',mode=owner.source_mode,
        episode_head=archive.head,render=render_proof,sources=_sources(),representation=REPRESENTATION,
        exact_artifact_independently_checked=True,owner_registered=False,training_approved=False,weights_updated=False)
    expected=pcc_lesson('Verified BW affine artifact repair',owner.model_contract_id,segments,archive_sha256=archive.head,
        verification_sha256=digest(proof),renderer_sha256=renderer.binding()['renderer_sha256'],tokenizer_sha256=renderer.tokenizer_id,
        skill_id='code.python.affine_clamp_fold',target_policy=record['target_policy'])
    if record['proof']!=proof or record['lesson']!=expected or record['tokens']!=tokens or _extract(completion,owner.source_mode)!=good:
        raise PracticeExportRefused('exact proof/lesson/token/mask/artifact derivation differs')
    return VerifiedBWExport(root,canonical(record))
