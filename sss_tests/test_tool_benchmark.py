import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from io import BytesIO
from sss.suites.tool_use import scenarios
from sss.tool_benchmark import run_scenario,Fixture,OpenAIModel

def call(name,args):return dict(role='assistant',content='',tool_calls=[dict(id='test',type='function',function=dict(name=name,arguments=json.dumps(args)))])

class Benchmark(unittest.TestCase):
    def setUp(self):self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
    def test_reference_scripts_exercise_every_owned_fixture(self):
        for scenario in scenarios():
            actions=[]
            for path in scenario.required_read:actions.append(('read_file',dict(path=path)))
            for path,text in scenario.expected.items():
                if path not in scenario.before:actions.append(('create_file',dict(path=path,content=text)))
                elif text!=scenario.before[path]:actions.append(('replace',dict(path=path,before=scenario.before[path],after=text)))
            if scenario.required_check:
                actions.append(('run_check',dict(name=scenario.required_check)))
                if scenario.id=='tasks.recover':actions.append(('run_check',dict(name=scenario.required_check)))
            actions.append(('finish',dict(answer=scenario.answer_contains or 'Done')))
            iterator=iter(actions)
            def model(messages,tools,intent):
                name,args=next(iterator);return call(name,args),{}
            result=run_scenario(scenario,model,self.root/scenario.id)
            self.assertEqual(result['status'],'pass',result)
    def test_unknown_backend_outcome_is_not_retried_or_turned_into_model_failure(self):
        count=[]
        def unavailable(*args):count.append(1);raise TimeoutError('controlled network uncertainty')
        result=run_scenario(scenarios()[0],unavailable,self.root/'unknown')
        self.assertEqual(result['status'],'unavailable');self.assertEqual(len(count),1)
    def test_invalid_model_arguments_fail_before_another_backend_request(self):
        count=[]
        def invalid(*args):count.append(1);return call('read_file',dict(path=12)),{}
        result=run_scenario(scenarios()[0],invalid,self.root/'invalid')
        self.assertEqual(result['status'],'fail');self.assertEqual(len(count),1)
    def test_mock_fixture_cannot_access_real_files_or_execute_shell(self):
        fixture=Fixture(scenarios()[0])
        self.assertEqual(fixture.call('read_file',dict(path='/etc/passwd'))['exit_code'],1)
        self.assertTrue(fixture.call('run_shell',dict(command='whoami'))['protocol_error'])
    def test_parallel_edit_and_finish_is_not_accepted_without_observed_results(self):
        def parallel(*args):
            one=call('create_file',dict(path='status.txt',content='ready\n'));one['tool_calls']+=call('finish',dict(answer='Done'))['tool_calls'];return one,{}
        self.assertEqual(run_scenario(scenarios()[1],parallel,self.root/'parallel')['status'],'fail')
    def test_request_intent_exists_before_post_without_auth_header(self):
        intent=self.root/'intent.json';seen=[]
        def transport(request,timeout):
            self.assertTrue(intent.exists());self.assertNotIn('private-test-key',intent.read_text())
            body=json.loads(request.data);self.assertEqual(body,json.loads(intent.read_text())['request'])
            self.assertEqual(request.get_header('Authorization'),'Bearer private-test-key')
            self.assertFalse(body['parallel_tool_calls']);self.assertEqual(body['temperature'],0)
            seen.append(request.full_url)
            return BytesIO(json.dumps(dict(choices=[dict(message=call('finish',dict(answer='Done')))],usage=dict(completion_tokens=3))).encode())
        with patch('urllib.request.urlopen',transport):
            message,usage=OpenAIModel('http://fixture.invalid/v1','cow','private-test-key')([],[],intent)
        self.assertEqual(seen,['http://fixture.invalid/v1/chat/completions'])
        self.assertEqual(message['tool_calls'][0]['function']['name'],'finish');self.assertEqual(usage['completion_tokens'],3)

if __name__=='__main__':unittest.main()
