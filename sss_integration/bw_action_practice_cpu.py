"""Reproduce verified action teaching on CPU; no inference or training.

Runs actual BW/COW/file/check boundaries with scripted proposals, then renders
the captured turns with the real local GGUF tokenizer/template. Preserves the
finished question/action/observation record privately for inspection.
"""
from pathlib import Path
import json
import os

from sss.records import canonical, digest, file_sha256
from sss.adapters.bw_verified_practice import PCCArtifactRenderer
from sss.adapters.bw_action_practice import PCCActionRenderer, export_action_correction, read_action_export
from sss.adapters.verified_practice_registry import InstalledBWPractice
from sss_integration.bw_verified_practice_cpu import captured_pair


def run(root, model):
    from serve.cow_http import model_text_components
    root=Path(root).absolute();root.mkdir(mode=0o700,parents=False,exist_ok=False)
    model_contract='a'*64  # Deliberate CPU fixture identity, not a serving-model claim.
    components=model_text_components(Path(model),dict(enable_thinking=False),model_contract_id=model_contract)
    renderer=PCCActionRenderer(components,model_contract_id=model_contract,
        tokenizer_sha256=PCCArtifactRenderer.tokenizer_identity(components),maximum_tokens=16384,stop_token_ids=[1,130073])
    check=('python3 -B -c \'from task import solve; '
           'assert solve([-4,0,2,9],3,-2,-5,8)=={"values":[-5,-2,4,8],"total":5}; '
           'assert solve([],1,2,0,9)=={"values":[],"total":0}\'')
    with captured_pair(root/'bw',check_command=check,finish_answer='The saved repair passed the behavior check.') as pair:
        owner=pair['owner'];left=pair['failure'].capture_id;right=pair['correction'].capture_id
        exported=export_action_correction(owner,pair['correction'].directory,correction_capture_id=right,
            failure_capture_id=left,renderer=renderer,output=root/'export')
    (root/'bw').rename(root/'hidden-original-bw')
    reread=read_action_export(root/'export',owner=owner,expected_export_id=exported.export_id,
        correction_capture_id=right,failure_capture_id=left,renderer=renderer)
    def write(path,value):
        fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        with os.fdopen(fd,'wb')as stream:stream.write(canonical(value)+b'\n')
    write(root/'owner-private.json',owner.descriptor())
    registrations=[dict(owner=owner.descriptor(),renderer=renderer.binding(),export_directory=str(root/'export'),
        export_id=reread.export_id,lesson_id=identity,turn_index=index,correction_capture_id=right,failure_capture_id=left)
        for index,identity in enumerate(reread.lesson_ids)]
    write(root/'registry-private.json',dict(schema=1,kind='sss.verified-bw-practice-registry.v1',registrations=registrations))
    installed=InstalledBWPractice(root/'registry-private.json',components=components,model_contract_id=model_contract)
    installed.validate_lessons([dict(lesson_id=digest(value),lesson=value) for value in reread.lessons])
    result=dict(schema=1,status='PASS',scope='Scripted CPU machinery, real BW/COW/OS and real MiniCPM tokenizer/template; not model learning',
        capture_ids=dict(failure=left,correction=right),export_id=reread.export_id,lesson_ids=reread.lesson_ids,
        renderer=renderer.binding(),examples=len(reread.lessons),
        context_lengths=[len(t['tokens']) for t in reread.tokens],
        selected_tokens=[sum(t['loss_mask']) for t in reread.tokens],
        finished_example_sha256=file_sha256(root/'export/finished-training-examples/example.txt'),
        export_receipt_sha256=file_sha256(root/'export/export-private.json'),
        source_sha256=dict(runner=file_sha256(__file__)),original_workspaces_required_for_readback=False,
        native_capacity_qualified=False,model_forward_calls=0,training_updates=0,gpu_used=False,
        serving_model_identity=False,owner_registered_in_cpu_fixture_only=True,production_training_approved=False)
    write(root/'result-public.json',result);return result


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True);parser.add_argument('--model',type=Path,required=True)
    args=parser.parse_args();print(json.dumps(run(args.output,args.model)))
