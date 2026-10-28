"""Real POSIX lease boundary; mocked GPU inventory/child, no model-quality claim."""
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch,Mock

@unittest.skipUnless(os.name=='posix','PCC native-oracle admission is a POSIX adapter')
class NativeOracle(unittest.TestCase):
    def setUp(self):
        from sss.adapters import native_oracle
        self.module=native_oracle;self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
    def test_idle_admission_holds_real_gpu_lease_and_passes_host_lease_to_child(self):
        import fcntl
        proc=Mock();proc.poll.return_value=0
        answers=['2, GPU-fixture, 80000, 0\n','GPU-fixture, 80000, 0\n']
        with (self.root/'worker.lock').open('a+') as worker:
            fcntl.flock(worker,fcntl.LOCK_EX)
            with patch.object(self.module.Path,'home',return_value=self.root),patch.object(self.module.subprocess,'check_output',side_effect=answers),patch.object(self.module.subprocess,'Popen',return_value=proc) as launch:
                with self.module.oracle_process('/fixture/oracle','/fixture/model','GPU-fixture',self.root/'oracle.log',extra_pass_fds=(worker.fileno(),)):
                    self.assertIn(worker.fileno(),launch.call_args.kwargs['pass_fds'])
                    with (self.root/'.local/state/context-cow/gpu-2.lock').open('a+') as second:
                        with self.assertRaises(BlockingIOError):fcntl.flock(second,fcntl.LOCK_EX|fcntl.LOCK_NB)
                self.assertEqual(launch.call_count,1)
    def test_rolling_utilization_wait_retains_the_same_zero_utilization_requirement(self):
        proc=Mock();proc.poll.return_value=0
        answers=['2, GPU-fixture, 80000, 10\n','GPU-fixture, 80000, 10\n','GPU-fixture, 80000, 0\n']
        with patch.object(self.module.Path,'home',return_value=self.root),patch.object(self.module.subprocess,'check_output',side_effect=answers),patch.object(self.module.time,'sleep') as wait,patch.object(self.module.subprocess,'Popen',return_value=proc) as launch:
            with self.module.oracle_process('/fixture/oracle','/fixture/model','GPU-fixture',self.root/'oracle.log'):pass
            self.assertEqual(wait.call_count,1);self.assertEqual(launch.call_count,1)
    def test_insufficient_headroom_never_starts_a_native_child(self):
        with patch.object(self.module.Path,'home',return_value=self.root),patch.object(self.module.subprocess,'check_output',side_effect=['2, GPU-fixture, 100, 0\n','GPU-fixture, 100, 0\n']),patch.object(self.module.time,'monotonic',side_effect=[0,31]),patch.object(self.module.subprocess,'Popen') as launch:
            with self.assertRaisesRegex(RuntimeError,'headroom'):
                with self.module.oracle_process('/fixture/oracle','/fixture/model','GPU-fixture',self.root/'oracle.log'):pass
            launch.assert_not_called()

    def test_explicit_shared_admission_and_larger_context_do_not_change_defaults(self):
        proc=Mock();proc.poll.return_value=0
        answers=['2, GPU-fixture, 14000, 90\n','GPU-fixture, 14000, 90\n']
        with patch.object(self.module.Path,'home',return_value=self.root),patch.object(self.module.subprocess,'check_output',side_effect=answers),patch.object(self.module.subprocess,'Popen',return_value=proc) as launch:
            with self.module.oracle_process('/fixture/oracle','/fixture/model','GPU-fixture',self.root/'oracle.log',context_tokens=512,batch_tokens=512,minimum_free_mib=8192,maximum_initial_utilization=100,all_logits=True):pass
            self.assertEqual(launch.call_args.args[0][2:4],['512','512'])
            self.assertEqual(launch.call_args.kwargs['env']['PCC_ORACLE_ALL_LOGITS'],'1')
    def test_invalid_resource_policy_is_refused_before_inventory_or_launch(self):
        with patch.object(self.module.subprocess,'check_output') as inventory,patch.object(self.module.subprocess,'Popen') as launch:
            for policy in [dict(context_tokens=64),dict(batch_tokens=512),dict(maximum_initial_utilization=101),dict(minimum_free_mib=0)]:
                with self.assertRaises(ValueError):
                    with self.module.oracle_process('/fixture/oracle','/fixture/model','GPU-fixture',self.root/'oracle.log',**policy):pass
            inventory.assert_not_called();launch.assert_not_called()

if __name__=='__main__':unittest.main()
