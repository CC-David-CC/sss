import unittest
from sss.suites.tool_use import scenarios,grade

def event(index,tool,arguments,code=0,disposition=None):
    return dict(operation_id='op-'+str(index),tool=tool,arguments=arguments,settled=True,exit_code=code,
                disposition=disposition or ('completion_requested' if tool=='finish' else 'exited' if tool=='run_check' else 'read' if tool=='read_file' else 'created'))

class Tools(unittest.TestCase):
    def setUp(self):self.cases={v.id:v for v in scenarios()}
    def test_read_requires_observation_and_observed_answer(self):
        c=self.cases['files.read']
        self.assertEqual(grade(c,[event(1,'finish',dict(answer='8127'))],c.expected)['status'],'fail')
        events=[event(1,'read_file',dict(path='service.conf')),event(2,'finish',dict(answer='port 8127'))]
        self.assertEqual(grade(c,events,c.expected)['status'],'pass')
        self.assertEqual(grade(c,[events[-1]],c.expected)['status'],'fail')
    def test_write_requires_actual_bytes_and_exact_scope(self):
        c=self.cases['files.write'];events=[event(1,'create_file',dict(path='status.txt')),event(2,'finish',dict(answer='done'))]
        self.assertEqual(grade(c,events,dict(status='claimed success'))['status'],'fail')
        self.assertEqual(grade(c,events,c.expected)['status'],'pass')
    def test_edit_requires_read_before_change_and_preserves_other_content(self):
        c=self.cases['files.edit'];change=event(2,'replace',dict(path='service.conf'))
        finish=event(3,'finish',dict(answer='done'));read=event(1,'read_file',dict(path='service.conf'))
        self.assertEqual(grade(c,[change,read,finish],c.expected)['status'],'fail')
        self.assertEqual(grade(c,[read,change,finish],c.expected)['status'],'pass')
        self.assertEqual(grade(c,[read,change,finish],{'service.conf':'port=9136\n'})['status'],'fail')
    def test_finish_requires_a_successful_check_after_last_mutation(self):
        c=self.cases['tasks.finish'];write=event(1,'create_file',dict(path='status.txt'))
        check=event(2,'run_check',dict(name='verify-status'));finish=event(3,'finish',dict(answer='done'))
        self.assertEqual(grade(c,[check,write,finish],c.expected)['status'],'fail')
        self.assertEqual(grade(c,[write,check,finish],c.expected)['status'],'pass')
        failed=event(4,'run_check',dict(name='verify-status'),1)
        self.assertEqual(grade(c,[write,check,failed,finish],c.expected)['status'],'fail')
    def test_recovery_needs_a_real_failed_then_passing_check(self):
        c=self.cases['tasks.recover'];events=[event(1,'read_file',dict(path='service.conf')),event(2,'run_check',dict(name='verify-port'),1),
            event(3,'replace',dict(path='service.conf')),event(4,'run_check',dict(name='verify-port')),event(5,'finish',dict(answer='done'))]
        self.assertEqual(grade(c,events,c.expected)['status'],'pass')
        self.assertEqual(grade(c,[v for v in events if v['operation_id']!='op-4'],c.expected)['status'],'fail')
    def test_unknown_effect_is_unavailable_not_a_training_failure(self):
        c=self.cases['files.write'];events=[event(1,'create_file',dict(path='status.txt')),event(2,'finish',dict(answer='done'))]
        events[0]['settled']=False
        self.assertEqual(grade(c,events,c.expected)['status'],'unavailable')
    def test_rejected_read_does_not_count_as_an_observation(self):
        c=self.cases['files.read'];events=[event(1,'read_file',dict(path='service.conf'),None,'rejected'),event(2,'finish',dict(answer='8127'))]
        self.assertEqual(grade(c,events,c.expected)['status'],'fail')
    def test_other_files_and_extra_mutations_are_detected(self):
        c=self.cases['files.scope'];events=[event(1,'create_file',dict(path='status.txt')),event(2,'finish',dict(answer='done'))]
        self.assertEqual(grade(c,events,c.expected)['status'],'pass')
        self.assertEqual(grade(c,events,dict(c.expected,**{'credentials.txt':'changed'}))['status'],'fail')
    def test_chained_action_requires_observed_input_before_write(self):
        c=self.cases['tasks.chain'];read=event(1,'read_file',dict(path='job.json'));write=event(2,'create_file',dict(path='report.txt'));finish=event(3,'finish',dict(answer='done'))
        self.assertEqual(grade(c,[write,read,finish],c.expected)['status'],'fail')
        self.assertEqual(grade(c,[read,write,finish],c.expected)['status'],'pass')
    def test_noisy_payload_requires_the_requested_field_not_a_nearby_number(self):
        c=self.cases['files.noisy_read'];read=event(1,'read_file',dict(path='inspection.json'))
        for answer in ['65500','81270']:
            self.assertEqual(grade(c,[read,event(2,'finish',dict(answer=answer))],c.expected)['status'],'fail')
        self.assertEqual(grade(c,[read,event(2,'finish',dict(answer='8127'))],c.expected)['status'],'pass')

if __name__=='__main__':unittest.main()
