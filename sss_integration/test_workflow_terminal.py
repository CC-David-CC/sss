"""Actual BW/PCC HTTP/ledger boundaries with scripted CPU proposals only."""
from pathlib import Path
import json,tempfile,unittest
from unittest.mock import patch

from sss.records import canonical,digest,file_sha256
from sss.paired import compare_frozen_evaluations,POLICY
from sss.artifact_assessment import ArtifactAssessmentCase
from sss.practice_oracle import AffineClampFoldCase
from sss_integration.test_workflow_recovery import fixture,PROFILE
from sss_integration.bw_verified_practice_cpu import BAD,ROWS


class TerminalWorkflowPanelTests(unittest.TestCase):
    def test_panel_archives_closed_false_workflows_and_continues(self):
        from sss_integration.workflow_evaluate import run
        from sss.adapters.workflow_evaluation import BWWorkflowEvaluator
        from branchwrite.coding_terminal_observation import read_unverified_archive
        from branchwrite.lesson_capture import CaptureRefused
        panel,backend,components,lease=fixture()
        panel.config.update(maximum_tokens=128,maximum_requests=2,maximum_steps=1024)
        panel.cases.append(ArtifactAssessmentCase(AffineClampFoldCase.install(
            'owned-second-budget-case','owned.budget-second',ROWS),BAD,'code.repair.affine','transfer_recovery'))
        panel.evaluation_id=digest([c.descriptor()for c in panel.cases])
        panel.expected_runtime=lambda profile:dict(scope='scripted-cpu-budget-panel')
        panel._summary=lambda value,candidate:compare_frozen_evaluations(value,value,POLICY)
        panel._command=lambda directory,profile:['explicit-scripted-cpu-child']
        # Only the deterministic proposal selector resets for a different case.
        # Native context, BW ledger and receipt paths use the real runtime.
        from branchwrite.coding_cli import save_launch as original_save
        instances=[]
        class Scripted(backend):
            def __init__(self,*a,**k):super().__init__(*a,**k);instances.append(self)
        def save(*args,**kwargs):
            for instance in instances:instance.cursor=0
            return original_save(*args,**kwargs)
        with tempfile.TemporaryDirectory()as tmp:
            root=Path(tmp);outer=root/'dispatch';outer.mkdir()
            (root/'profile.json').write_bytes(canonical(PROFILE));(root/'candidate.json').write_bytes(b'null')
            with (patch('sss_integration.workflow_evaluate.BWWorkflowEvaluator',lambda path:panel),
                  patch('sss_integration.workflow_evaluate.cow_gpu_admission',lease),
                  patch('context_time_travel.llama_dense_backend.LlamaDenseBackend',Scripted),
                  patch('branchwrite.coding_cli.save_launch',save),
                  patch('serve.cow_http.model_text_components',lambda *a,**k:components)):
                value=run(root/'unused-owner',root/'profile.json',root/'candidate.json',outer/'evaluation',
                    expected_evaluator_id=panel.identity)
            self.assertEqual((value['status'],value['cases'],value['passed'],value['finished']),('COMPLETE',2,0,0))
            settled=json.loads((outer/'evaluation/settlement.json').read_bytes())
            self.assertEqual(settled['result_sha256'],file_sha256(outer/'evaluation/result.json'))
            for index in range(2):
                folder=outer/'evaluation'/('%04d'%index)
                self.assertFalse((folder/'capture').exists());self.assertFalse((folder/'oracle').exists())
                observed=json.loads((folder/'observation-private.json').read_bytes())
                self.assertEqual(observed['terminal']['status'],'terminal_unverified')
                self.assertFalse(observed['terminal']['training_eligible'])
                self.assertEqual(observed['oracle_status'],'not_run_unverified_workflow')
                # The original workflow can be retained elsewhere or continued;
                # its frozen failure remains independently readable.
                (folder/'state').rename(folder/'original-state-retired')
            (outer/'adapter-intent-private.json').write_bytes(canonical(dict(schema=1,
                evaluator_id=panel.identity,profile=PROFILE,command=panel._command(outer,PROFILE),no_implicit_retry=True)))
            (outer/'candidate-profile.json').write_bytes(canonical(PROFILE))
            (outer/'candidate-selection-private.json').write_bytes(b'null')
            with patch('branchwrite.cow_client.HTTPTransport.request',side_effect=AssertionError('read-only regrade')):
                self.assertEqual(BWWorkflowEvaluator._evidence(panel,None,outer),value)
                archive=outer/'evaluation/0000/terminal'
                self.assertFalse(read_unverified_archive(archive)['world_artifacts_captured'])
                # Changing original launch bindings cannot borrow a valid archive.
                from sss.workflow_assessment import observe_terminal_failure
                launch=json.loads((archive/'state/coding-launch.json').read_bytes())['launch']
                launch['config']['profiles']['control']['max_requests']=3
                with self.assertRaisesRegex(ValueError,'launch changed'):
                    observe_terminal_failure(panel.cases[0],archive,launch)
                path=archive/'state/cow-operations'
                journal=next(path.iterdir());journal.chmod(0o600);journal.write_bytes(journal.read_bytes()+b' ')
                with self.assertRaisesRegex(CaptureRefused,'evidence changed'):read_unverified_archive(archive)


if __name__=='__main__':unittest.main()
