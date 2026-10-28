"""Verified BW action practice using the original tool turns and PCC append rules.

BW validates workflow evidence; S3 checks an owned practice artifact independently;
PCC supplies model-specific rendering and lesson tokenization. Nothing dispatches
inference, approves membership or trains from this module.
"""
import copy
import hashlib
from pathlib import Path

from sss.records import canonical, digest, file_sha256
from sss.profiles import TARGET_POLICIES
from sss.episodes import EpisodeArchive, export_text
from sss.adapters.episode_lessons import pcc_lesson
from sss.adapters.bw_verified_practice import (
    BWArtifactPractice, PracticeExportRefused, _captures, _copy_capture,
    _oracle, _inventory, _write, _read, _hex, _sources, strict_json, observe)

REPRESENTATION = 'bw-captured-tool-actions-v1'
KIND = 'sss.bw-verified-action-export.v1'


class PCCActionRenderer:
    """Metadata-only renderer; uses the actual PCC initial/continuing append API.

    Previously consumed outputs are never re-rendered. Each returned lesson has
    one selected action through EOS, with all prior actions and tool results masked.
    Thinking trajectories are deliberately not claimed by this text-only adapter.
    """
    def __init__(self, components, *, model_contract_id, tokenizer_sha256, maximum_tokens, stop_token_ids):
        from serve.cow_renderer import renderer_identity_receipt
        _hex(model_contract_id); _hex(tokenizer_sha256)
        self.tokenizer = components['tokenizer']; self.encoder = components['render'].__self__
        self.model = model_contract_id; self.tokenizer_id = tokenizer_sha256
        if (self.encoder.template_kwargs != {'enable_thinking': False}
                or type(maximum_tokens) is not int or not 2 <= maximum_tokens <= 131072
                or type(stop_token_ids) not in (list, tuple) or not stop_token_ids
                or any(type(i) is not int or i < 0 for i in stop_token_ids)
                or list(stop_token_ids) != sorted(set(stop_token_ids))):
            raise PracticeExportRefused('qualified non-thinking renderer, exact stops and finite token bound required')
        self.maximum = maximum_tokens; self.stops = tuple(stop_token_ids)
        receipt = renderer_identity_receipt(self.tokenizer, self.encoder.template.source,
            self.encoder.template_kwargs, model_contract_id=model_contract_id,
            **(dict(tool_binding=self.encoder.tool_binding) if getattr(self.encoder, 'tool_binding', None) is not None else {}))
        if (digest(receipt['tokenizer']) != tokenizer_sha256
                or components.get('renderer_id') != digest(receipt)):
            raise PracticeExportRefused('actual PCC renderer/tokenizer identity differs')
        self._receipt = receipt
        self._binding = canonical(dict(schema=1, kind='pcc-bw-action-through-eos-renderer-v1',
            model_contract_id=self.model, renderer_sha256=digest(receipt), tokenizer_sha256=self.tokenizer_id,
            maximum_tokens=self.maximum, stop_token_ids=list(self.stops), representation=REPRESENTATION,
            adapter_sha256=file_sha256(__file__), pcc_sources_sha256=self._pcc_sources()))

    def _pcc_sources(self):
        import serve.cow_prompt_encoder as base
        import serve.server as service
        import tools.pcc_lesson_segments as lesson
        import inspect
        return {name:file_sha256(path) for name,path in dict(base=base.__file__, service=service.__file__,
            lesson=lesson.__file__, encoder=inspect.getfile(type(self.encoder))).items()}

    def binding(self): return strict_json(self._binding)

    def verify(self):
        from serve.cow_renderer import renderer_identity_receipt
        receipt = renderer_identity_receipt(self.tokenizer, self.encoder.template.source,
            self.encoder.template_kwargs, model_contract_id=self.model,
            **(dict(tool_binding=self.encoder.tool_binding) if getattr(self.encoder, 'tool_binding', None) is not None else {}))
        bound = self.binding()
        if (receipt != self._receipt or self.encoder.template_kwargs != {'enable_thinking': False}
                or self._pcc_sources() != bound['pcc_sources_sha256']
                or file_sha256(__file__) != bound['adapter_sha256'] or self.model != bound['model_contract_id']
                or self.tokenizer_id != bound['tokenizer_sha256'] or self.maximum != bound['maximum_tokens']
                or list(self.stops) != bound['stop_token_ids']):
            raise PracticeExportRefused('action renderer implementation or inputs changed')

    def render(self, exported, *, target_policy):
        from tools.pcc_lesson_segments import tokenize_segments
        self.verify()
        if target_policy not in TARGET_POLICIES:
            raise PracticeExportRefused('unsupported target policy')
        messages = exported['bootstrap_messages']; turns = exported['turns']
        texts = [m['content'] for m in messages] + [t[k] for t in turns for k in ('user_content','assistant_text')]
        special = getattr(self.tokenizer, 'special_tokens', ())
        if any(s and s in text for s in special for text in texts):
            raise PracticeExportRefused('literal model control requires a separately qualified representation')
        root_text = self.encoder.render(messages, add_generation_prompt=False)
        ids = list(self.encoder.encode_rendered(messages, root_text, False))
        if self.encoder.initial_root_mode(ids, {'status':'idle'}) != 'context_only':
            raise PracticeExportRefused('actual PCC root is not a context-only boundary')
        stop = self.tokenizer.encode('<|im_end|>', parse_special=True)
        if len(stop) != 1 or stop[0] not in self.stops:
            raise PracticeExportRefused('actual model needs an admitted single chat-frame EOS')
        segments = [dict(role='system',kind='instruction',rendered=self.tokenizer.decode(ids),verified=False,scope='practice')]
        rendered = []
        for index, turn in enumerate(turns):
            append = self.encoder.append_initial_user_suffix if index == 0 else self.encoder.append_user_suffix
            controller = {'status':'idle'} if index == 0 else {'status':'stopped','policy':{'eos_tokens':list(self.stops)}}
            suffix = list(append(tuple(ids), controller, turn['user_content']))
            ids.extend(suffix)
            segments.append(dict(role='user',kind='question' if index == 0 else 'observation',
                rendered=self.tokenizer.decode(suffix),verified=False,scope='practice'))
            action = self.tokenizer.encode(turn['assistant_text'], parse_special=False) + stop
            if self.tokenizer.decode(action[:-1]) != turn['assistant_text'] or any(t in self.stops for t in action[:-1]):
                raise PracticeExportRefused('exact original action body and single native stop required')
            segments.append(dict(role='assistant',kind='answer' if index == len(turns)-1 else 'action',
                rendered=self.tokenizer.decode(action),verified=True,scope='practice'))
            ids.extend(action)
            skeleton = pcc_lesson('Verified BW tool action',self.model,copy.deepcopy(segments),
                archive_sha256='0'*64,verification_sha256='0'*64,renderer_sha256=self.binding()['renderer_sha256'],
                tokenizer_sha256=self.tokenizer_id,skill_id='agency.bw.checked_file_repair',target_policy=target_policy)
            tokens = tokenize_segments(skeleton,lambda text:self.tokenizer.encode(text,parse_special=True),self.maximum)
            if tokens['tokens'] + [tokens['targets'][-1]] != ids:
                raise PracticeExportRefused('lesson tokens differ from actual PCC append-only history')
            selected = [t for t,on in zip(tokens['targets'],tokens['loss_mask']) if on]
            if selected != action:
                raise PracticeExportRefused('only the current action through EOS may be supervised')
            rendered.append((copy.deepcopy(segments),tokens,dict(turn_index=index,
                action_sha256=hashlib.sha256(turn['assistant_text'].encode()).hexdigest(),
                prefix_tokens=len(ids)-len(action),selected_tokens=len(action),eos_token_id=stop[0],
                append_only_history_verified=True,tool_feedback_always_masked=True,no_thinking_targets=True)))
            # Previous teacher turns remain exact context for the next example.
            segments[-1] = dict(segments[-1],kind='framing',verified=False)
        return rendered


def _turns(owner, capture, renderer):
    from branchwrite.lesson_actions import captured_action_turns
    value = captured_action_turns(capture.directory, expected_capture_id=capture.capture_id)
    turns = value['turns']
    if ([t['action']['tool'] for t in turns] != ['read_file','replace','run_check','finish']
            or turns[0]['action']['arguments'] != {'path':'task.py'}
            or turns[1]['action']['arguments'].get('path') != 'task.py'
            or turns[2]['outcome']['exit_code'] != 0):
        raise PracticeExportRefused('initial supported practice is one read/edit/check/finish repair')
    texts = [m['content'] for m in value['bootstrap_messages']]
    texts += [t[key] for t in turns for key in ('user_content','assistant_text')]
    teaching = '\n'.join(texts)
    if any(text in teaching for text in owner.protected_texts):
        raise PracticeExportRefused('protected material cannot enter action context or targets')
    ids = renderer.tokenizer.encode(teaching,parse_special=False)
    for text in owner.protected_texts:
        needle = renderer.tokenizer.encode(text,parse_special=False)
        if needle and any(ids[i:i+len(needle)] == needle for i in range(len(ids)-len(needle)+1)):
            raise PracticeExportRefused('protected token material cannot enter action practice')
    return value


def _derive(owner, root, renderer, correction_id, failure_id, target_policy):
    failed, corrected, bad, good = _captures(owner,root/'capture',correction_id,failure_id)
    left = _oracle(owner.case,bad,root/'failed-oracle','fail')
    right = _oracle(owner.case,good,root/'corrected-oracle','pass')
    turns = _turns(owner,corrected,renderer)
    rendered = renderer.render(turns,target_policy=target_policy)
    archive = EpisodeArchive(root/'episode')
    expected_events = [('system','instruction',m['content'],False,'practice') for m in turns['bootstrap_messages']]
    for index, turn in enumerate(turns['turns']):
        expected_events.extend([('user','question' if index == 0 else 'observation',turn['user_content'],False,'practice'),
                                ('assistant','answer' if index == len(turns['turns'])-1 else 'action',turn['assistant_text'],True,'practice')])
    if [(e['role'],e['kind'],e['text'],e['verified'],e['scope']) for e in archive.records()] != expected_events:
        raise PracticeExportRefused('archived action teaching differs from original BW inputs/outputs')
    from sss.episodes import render_text
    if _read(root/'finished-training-examples/example.txt') != render_text(archive,public=False):
        raise PracticeExportRefused('saved finished example differs from original action episode')
    proof = dict(schema=1,kind='sss.bw-action-proof.v1',owner_binding_sha256=digest(owner.binding()),
        failure_oracle_evidence_sha256=left['evidence_sha256'],correction_oracle_evidence_sha256=right['evidence_sha256'],
        failed_source_sha256=hashlib.sha256(bad).hexdigest(),corrected_source_sha256=hashlib.sha256(good).hexdigest(),
        captured_action_turns_sha256=digest(turns),episode_head=archive.head,representation=REPRESENTATION,
        sources=dict(artifact=_sources(),adapter=file_sha256(__file__),bw_action_reader_sha256=turns['source_sha256']),
        render=[r[2] for r in rendered],exact_artifact_independently_checked=True,
        owner_registered=False,training_approved=False,weights_updated=False)
    lessons = [pcc_lesson('Verified BW tool action '+str(i+1),owner.model_contract_id,spans,
        archive_sha256=archive.head,verification_sha256=digest(proof),renderer_sha256=renderer.binding()['renderer_sha256'],
        tokenizer_sha256=renderer.tokenizer_id,skill_id='agency.bw.checked_file_repair',target_policy=target_policy)
        for i,(spans,_,_) in enumerate(rendered)]
    return proof,lessons,[r[1] for r in rendered]


class VerifiedBWActionExport:
    def __init__(self, directory, value): self.directory=directory; self._data=canonical(value)
    @property
    def export_id(self): return strict_json(self._data)['export_id']
    @property
    def lessons(self): return strict_json(self._data)['lessons']
    @property
    def lesson_ids(self): return [digest(lesson) for lesson in self.lessons]
    @property
    def tokens(self): return strict_json(self._data)['tokens']
    def binding(self):
        value=strict_json(self._data)
        return dict(kind=KIND,export_id=self.export_id,lesson_ids=self.lesson_ids,
            proof_sha256=digest(value['proof']),representation=REPRESENTATION,owner_registered=False,training_approved=False)


def export_action_correction(owner, correction_capture, *, correction_capture_id, failure_capture_id, renderer, output, target_policy='actions_answer'):
    if type(owner) is not BWArtifactPractice or type(renderer) is not PCCActionRenderer or renderer.model != owner.model_contract_id:
        raise PracticeExportRefused('installed owner and actual model action renderer required')
    failed, corrected, bad, good = _captures(owner,correction_capture,correction_capture_id,failure_capture_id)
    # Prove representation/split/context before copying or running an oracle.
    turns = _turns(owner,corrected,renderer); renderer.render(turns,target_policy=target_policy)
    root=Path(output).absolute()
    from branchwrite.lesson_capture import _real_path
    _real_path(root.parent)
    if root.exists() or root.is_symlink() or root.is_relative_to(corrected.directory) or corrected.directory.is_relative_to(root):
        raise PracticeExportRefused('fresh nonoverlapping action export required')
    root.mkdir(mode=0o700); _copy_capture(corrected,root/'capture')
    observe(owner.case,bad,hashlib.sha256(bad).hexdigest(),root/'failed-oracle')
    observe(owner.case,good,hashlib.sha256(good).hexdigest(),root/'corrected-oracle')
    archive=EpisodeArchive(root/'episode',create=True,metadata=dict(origin='independently-checked-bw-actions',representation=REPRESENTATION))
    for m in turns['bootstrap_messages']:archive.append('system','instruction',m['content'],scope='practice')
    for index,turn in enumerate(turns['turns']):
        archive.append('user','question' if index == 0 else 'observation',turn['user_content'],scope='practice')
        archive.append('assistant','answer' if index == len(turns['turns'])-1 else 'action',turn['assistant_text'],verified=True,scope='practice')
    (root/'finished-training-examples').mkdir(mode=0o700)
    export_text(archive,root/'finished-training-examples/example.txt',public=False)
    proof, lessons, tokens = _derive(owner,root,renderer,correction_capture_id,failure_capture_id,target_policy)
    record=dict(schema=1,kind=KIND,owner=owner.binding(),renderer=renderer.binding(),
        correction_capture_id=correction_capture_id,failure_capture_id=failure_capture_id,target_policy=target_policy,
        proof=proof,lessons=lessons,tokens=tokens,files=_inventory(root),owner_registered=False,training_approved=False)
    record['export_id']=digest(record); _write(root/'export-private.json',record)
    return read_action_export(root,owner=owner,expected_export_id=record['export_id'],correction_capture_id=correction_capture_id,
        failure_capture_id=failure_capture_id,renderer=renderer)


def read_action_export(directory, *, owner, expected_export_id, correction_capture_id, failure_capture_id, renderer):
    """Recompute original evidence, rendered tokens and masks; no tool/model calls."""
    if type(owner) is not BWArtifactPractice or type(renderer) is not PCCActionRenderer or renderer.model != owner.model_contract_id:
        raise PracticeExportRefused('installed owner and actual model action renderer required')
    _hex(expected_export_id); root=Path(directory).absolute(); record=strict_json(_read(root/'export-private.json'))
    keys={'schema','kind','owner','renderer','correction_capture_id','failure_capture_id','target_policy',
          'proof','lessons','tokens','files','owner_registered','training_approved','export_id'}
    if (type(record) is not dict or set(record) != keys or type(record['schema']) is not int or record['schema'] != 1
            or record['kind'] != KIND or record['export_id'] != expected_export_id
            or expected_export_id != digest({k:v for k,v in record.items() if k != 'export_id'})
            or record['owner'] != owner.binding() or record['renderer'] != renderer.binding()
            or record['correction_capture_id'] != correction_capture_id or record['failure_capture_id'] != failure_capture_id
            or record['owner_registered'] is not False or record['training_approved'] is not False):
        raise PracticeExportRefused('action export differs from exact installed owner inputs')
    if [row for row in _inventory(root) if row['path'] != 'export-private.json'] != record['files']:
        raise PracticeExportRefused('original action export files changed or are incomplete')
    proof,lessons,tokens = _derive(owner,root,renderer,correction_capture_id,failure_capture_id,record['target_policy'])
    if record['proof'] != proof or record['lessons'] != lessons or record['tokens'] != tokens:
        raise PracticeExportRefused('exact action proof, lessons, tokens or masks differ')
    return VerifiedBWActionExport(root,record)


def main(argv=None):
    """Explicit owner-side export/audit command; never installs or trains."""
    import argparse
    from sss.adapters.owner_configuration import read_private_json
    from sss.adapters.bw_verified_practice import PCCArtifactRenderer
    from serve.cow_http import model_text_components
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation',choices=('export','audit'))
    parser.add_argument('--owner',type=Path,required=True,help='Private BWArtifactPractice descriptor')
    parser.add_argument('--model',type=Path,required=True,help='Local GGUF for tokenizer/template metadata only')
    parser.add_argument('--correction-capture',type=Path)
    parser.add_argument('--correction-capture-id',required=True)
    parser.add_argument('--failure-capture-id',required=True)
    parser.add_argument('--directory',type=Path,required=True,help='Fresh export directory, or original directory to audit')
    parser.add_argument('--export-id',help='Required exact owner pin for audit')
    parser.add_argument('--maximum-tokens',type=int,required=True,help='Refuse longer examples; never truncate')
    parser.add_argument('--stop-token-ids',type=int,nargs='+',required=True)
    parser.add_argument('--target-policy',choices=TARGET_POLICIES,default='actions_answer')
    args=parser.parse_args(argv)
    if args.operation=='export' and (args.correction_capture is None or args.export_id is not None):
        parser.error('export requires a correction capture and does not accept a claimed export identity')
    if args.operation=='audit' and (args.export_id is None or args.correction_capture is not None):
        parser.error('audit requires the original export identity and reads its embedded capture')
    _,_,descriptor=read_private_json(args.owner,maximum_bytes=16*1024**2)
    owner=BWArtifactPractice.from_descriptor(descriptor)
    components=model_text_components(args.model,dict(enable_thinking=False),model_contract_id=owner.model_contract_id)
    renderer=PCCActionRenderer(components,model_contract_id=owner.model_contract_id,
        tokenizer_sha256=PCCArtifactRenderer.tokenizer_identity(components),maximum_tokens=args.maximum_tokens,
        stop_token_ids=args.stop_token_ids)
    kwargs=dict(owner=owner,renderer=renderer,correction_capture_id=args.correction_capture_id,failure_capture_id=args.failure_capture_id)
    if args.operation=='export':
        exported=export_action_correction(correction_capture=args.correction_capture,output=args.directory,
            target_policy=args.target_policy,**kwargs)
    else:
        exported=read_action_export(args.directory,expected_export_id=args.export_id,**kwargs)
    print(canonical(dict(status='VERIFIED_EXPORT',operation=args.operation,**exported.binding(),
        examples=len(exported.lessons),training_updates=0,model_forward_calls=0)).decode())
    return 0


if __name__=='__main__':raise SystemExit(main())
