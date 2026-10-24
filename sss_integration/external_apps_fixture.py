"""Actual pinned CLIs, deterministic protocol replies, real file/tool effects.

The host launcher supplies an isolated Linux namespace. No model is called.
"""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time


VERSIONS = {'codex': '0.164.0', 'opencode': '2.1.4', 'pi': '1.4.0'}
PROMPT = ('Read app.py. Write notes.txt containing exactly "read, write, edit, verify" '
          'followed by a newline. Repair double(n) to return twice n, verify it, '
          'then report completion. Work only in this prepared project.')
COMMANDS = [
    'cat /work/app.py',
    "python3 -c \"from pathlib import Path;Path('/work/notes.txt').write_text('read, write, edit, verify\\n')\"",
    "python3 -c \"from pathlib import Path;p=Path('/work/app.py');p.write_text(p.read_text().replace('return n','return 2*n'))\"",
    "python3 -c \"import app;assert app.double(21)==42;assert app.double(-3)==-6;print('SSS_VERIFIED_42')\"",
]


class Fixture:
    def __init__(self, app):
        self.app = app
        self.requests = []
        self.calls = []
        self.failures = []
        self.lock = threading.Lock()

    def reply(self, path, body):
        self.requests.append(dict(path=path, body=body))
        assert len(self.requests) <= 5, 'Unexpected extra model request'
        assert body['model'] == 'wen-fixture' and body['stream'] is True
        if self.app == 'codex':
            assert path == '/v1/responses' and body.get('store') is False
            responses.check_request(body)
            responses.input_messages(body)
            tools, names, skipped = responses.request_tools(body)
            assert not skipped, 'Hosted tool omitted by PCC'
            results = {i.get('call_id'): i.get('output') for i in body.get('input', [])
                       if i.get('type') in ('function_call_output', 'custom_tool_call_output')}
        else:
            assert path == '/v1/chat/completions'
            tools = [t.get('function', t) for t in body.get('tools', [])]
            names = {}
            results = {m.get('tool_call_id'): m.get('content') for m in body['messages'] if m.get('role') == 'tool'}
        step = len(self.calls)
        if step:
            previous = self.calls[-1]
            assert previous['id'] in results, 'Original tool result missing from continuation'
            text = json.dumps(results[previous['id']])
            if step == 1:
                assert 'return n' in text, 'Read result did not reach the next model request'
            if step == 4:
                assert 'SSS_VERIFIED_42' in text, 'Verification did not reach the next model request'
        if step == 4:
            return self.encode(body, names, None, 'Completed the repair and verification.')
        assert tools, 'No executable tools advertised'
        call = self.tool_call(tools, step)
        self.calls.append(call)
        return self.encode(body, names, call, '')

    def tool_call(self, tools, step):
        by_name = {t['name']: t for t in tools}
        if self.app == 'codex':
            name = next(n for n in by_name if n.split('.')[-1] in ('exec_command', 'shell_command'))
            props = by_name[name]['parameters']['properties']
            key = 'cmd' if 'cmd' in props else 'command'
            arguments = {key: COMMANDS[step]}
            if 'workdir' in props:
                arguments['workdir'] = '/work'
            if 'yield_time_ms' in props:
                arguments['yield_time_ms'] = 1000
        else:
            name = ('read', 'write', 'edit', 'shell' if self.app == 'opencode' else 'bash')[step]
            assert name in by_name, 'Required native tool missing: ' + name
            if self.app == 'pi':
                arguments = [dict(path='/work/app.py'),
                    dict(path='/work/notes.txt', content='read, write, edit, verify\n'),
                    dict(path='/work/app.py', edits=[dict(oldText='return n', newText='return 2*n')]),
                    dict(command=COMMANDS[3])][step]
            else:
                arguments = [dict(path='/work/app.py'),
                    dict(path='/work/notes.txt', content='read, write, edit, verify\n'),
                    dict(path='/work/app.py', oldString='return n', newString='return 2*n'),
                    dict(command=COMMANDS[3], workdir='/work', timeout=10000)][step]
        schema = by_name[name].get('parameters') or {}
        assert set(schema.get('required', [])) <= arguments.keys(), 'Required native argument missing'
        assert set(arguments) <= schema.get('properties', {}).keys(), 'Unexpected native tool argument'
        return dict(id='call_sss_' + str(step), name=name, arguments=arguments)

    def encode(self, body, names, call, text):
        if self.app == 'codex':
            assembler = responses.Assembler(body, 'wen-fixture', 23, names, True)
            events = assembler.start()
            event = (Event('tool_call', call=ToolCall(call['name'], call['arguments'], call['id']))
                     if call else Event('content', text))
            events += assembler.feed(event)
            events += assembler.finish(dict(finish='tool_calls' if call else 'stop', prompt_tokens=23, completion_tokens=9))
            return ''.join('event: ' + e['type'] + '\ndata: ' + json.dumps(e) + '\n\n' for e in events).encode()
        delta = dict(role='assistant')
        if call:
            delta['tool_calls'] = [dict(index=0, id=call['id'], type='function',
                function=dict(name=call['name'], arguments=json.dumps(call['arguments'])))]
        else:
            delta['content'] = text
        base = dict(id='fixture-' + str(len(self.requests)), object='chat.completion.chunk', created=1, model='wen-fixture')
        packets = [dict(base, choices=[dict(index=0, delta=delta, finish_reason=None)]),
            dict(base, choices=[dict(index=0, delta={}, finish_reason='tool_calls' if call else 'stop')]),
            dict(base, choices=[], usage=dict(prompt_tokens=23, completion_tokens=9, total_tokens=32))]
        return (''.join('data: ' + json.dumps(p) + '\n\n' for p in packets) + 'data: [DONE]\n\n').encode()


def configuration(app, port, *, model='wen-fixture', context=8192, prompt=None, disable_delegation=False, stream_idle_ms=10000):
    base = 'http://127.0.0.1:' + str(port) + '/v1'
    prompt = PROMPT if prompt is None else prompt
    if app == 'hermes':
        directory=Path('/work/hermes-home');directory.mkdir(mode=0o700)
        config=dict(_config_version=52,model=dict(default=model,provider='custom',base_url=base,api_key='fixture-not-a-secret',
                              context_length=context,streaming=True),
                    auxiliary=dict(title_generation=dict(enabled=False),stream_only_base_urls=[base]),
                    agent=dict(max_turns=12,run_budget_seconds=85),memory=dict(memory_enabled=False,user_profile_enabled=False))
        # JSON is valid YAML. No owner home, fallback credential or auxiliary endpoint is mounted.
        (directory/'config.yaml').write_text(json.dumps(config,indent=2)+'\n')
        return ['/tools/bin/python','/tools/bin/hermes','chat','--query-file','/work/instruction.txt',
                '--oneshot','--format','stream-json','--provider','custom','--base-url',base,
                '--api-key','fixture-not-a-secret','--model',model,'--reasoning','none','--toolsets','terminal,file',
                '--max-turns','12','--ignore-rules','--yolo','--in','/work']
    if app == 'qwen':
        os.environ.update(OPENAI_API_KEY='fixture-not-a-secret',OPENAI_BASE_URL=base,OPENAI_MODEL=model,
                          QWEN_CODE_MAX_OUTPUT_TOKENS='512')
        directory=Path('/work/.qwen');directory.mkdir(mode=0o700)
        config=dict(security=dict(auth=dict(selectedType='openai')),telemetry=dict(enabled=False),
            modelProviders=dict(openai=[dict(id=model,name='Pinned local model',baseUrl=base,
                envKey='OPENAI_API_KEY',generationConfig=dict(contextWindowSize=context,maxRetries=0,
                    samplingParams=dict(temperature=0,seed=0,max_tokens=512)))]))
        (directory/'settings.json').write_text(json.dumps(config,indent=2)+'\n')
        return ['/usr/bin/node','/tools/node_modules/@qwen-code/qwen-code/cli-entry.js','--bare',
                '--model',model,'--auth-type','openai','--openai-base-url',base,
                '--openai-api-key','fixture-not-a-secret','--advisor','off','--approval-mode','yolo',
                '--max-session-turns','12','--max-tool-calls','12','--max-wall-time','85s',
                '--output-format','stream-json',prompt]
    if app == 'dsh':
        os.environ.update(DSH_HOME='/work/dsh-home',DSH_TELEMETRY_DISABLED='1',
                          DSH_PERMISSION_MODE='danger-full-access',SSS_MODEL_KEY='fixture-not-a-secret')
        patches=[dict(id='llm-pi-ai',config=dict(providers={'sss-local':dict(api='openai-completions',
            baseURL=base,apiKeyEnv='SSS_MODEL_KEY',defaultContextWindow=context,defaultMaxTokens=512,
            retryPolicy=dict(mode='normal',maxRetries=0),compat=dict(supportsStore=False,
                supportsDeveloperRole=False,supportsReasoningEffort=False,maxTokensField='max_tokens'),
            models=[dict(id=model,contextWindow=context,maxTokens=512,reasoningEfforts=False)])})),
            dict(id='agent-default-model',config=dict(provider='sss-local',model=model)),
            *[dict(id=name,disabled=True) for name in ('session-title-llm','tool-subagent-control',
                'tool-subagent-list-agents','tool-subagent','tool-subagent-fork')]]
        Path('/work/dsh.patch.json').write_text(json.dumps(patches,indent=2)+'\n')
        return ['/usr/bin/node','/tools/node_modules/@deepseek-ai/dsh/lib/bin.js',
                '--profile','headless','--patch','/work/dsh.patch.json','--json',prompt]
    if app == 'codex':
        directory = Path('/work/.codex'); directory.mkdir(mode=0o700)
        (directory/'config.toml').write_text('''model = "wen-fixture"
model_provider = "pcc_fixture"
model_context_window = 8192
model_reasoning_effort = "none"
model_reasoning_summary = "none"
approval_policy = "never"
sandbox_mode = "danger-full-access"
web_search = "disabled"
[model_providers.pcc_fixture]
name = "Local PCC protocol fixture"
base_url = "BASE"
wire_api = "responses"
requires_openai_auth = false
supports_websockets = false
request_max_retries = 0
stream_max_retries = 0
stream_idle_timeout_ms = 10000
'''.replace('BASE', base).replace('"wen-fixture"', json.dumps(model)).replace('model_context_window = 8192', 'model_context_window = '+str(context)).replace('stream_idle_timeout_ms = 10000', 'stream_idle_timeout_ms = '+str(stream_idle_ms))
            + ('\n[features]\nmulti_agent = false\ncollab = false\nmulti_agent_v2 = false\nenable_fanout = false\n' if disable_delegation else ''))
        return ['/usr/bin/node', '/tools/node_modules/@openai/codex/bin/codex.js', 'exec',
                '--strict-config', '--skip-git-repo-check', '--ephemeral', '--json', prompt]
    if app == 'opencode':
        config = dict(model='pccfixture/'+model, small_model='pccfixture/'+model,
            enabled_providers=['pccfixture'], permission={'*': 'deny', 'read': 'allow', 'write': 'allow', 'edit': 'allow', 'shell': 'allow'},
            provider=dict(pccfixture=dict(name='Local protocol fixture', npm='@ai-sdk/openai-compatible',
                options=dict(baseURL=base, apiKey='fixture-not-a-secret'),
                models={model: dict(name='Pinned local model', limit=dict(context=context, output=512))})))
        Path('/work/opencode.json').write_text(json.dumps(config, indent=2) + '\n')
        return ['/tools/node_modules/@opencode/cli/bin/opencode.exe', 'run', '--standalone', '--format', 'json',
                '--title', 'SSS bounded client check', '--model', 'pccfixture/'+model, prompt]
    directory = Path('/work/.pi/agent'); directory.mkdir(mode=0o700, parents=True)
    config = dict(providers=dict(pcc_fixture=dict(api='openai-completions', baseUrl=base,
        apiKey='fixture-not-a-secret', authHeader=True,
        compat=dict(supportsStore=False, supportsDeveloperRole=False, supportsReasoningEffort=False, maxTokensField='max_tokens'),
        models=[dict(id=model, name='Pinned local model', reasoning=False, input=['text'], contextWindow=context,
            maxTokens=512, cost=dict(input=0, output=0, cacheRead=0, cacheWrite=0),
            samplingParams=dict(temperature=0, seed=0, parallel_tool_calls=False))])))
    (directory/'models.json').write_text(json.dumps(config, indent=2) + '\n')
    return ['/usr/bin/node', '/tools/node_modules/@earendil-works/pi-coding-agent/dist/bundle/cli.js',
        '--provider', 'pcc_fixture', '--model', model, '--thinking', 'off', '--tools', 'read,write,edit,bash',
        '--no-session', '--no-extensions', '--no-mcp', '--no-skills', '--no-prompt-templates', '--no-themes',
        '--no-context-files', '--mode', 'json', '--print', prompt]


def main():
    if os.environ.get('SSS_ISOLATED_TRANSPORT_FIXTURE') != '1' or Path.cwd() != Path('/work'):
        raise RuntimeError('Use the host launcher and its disposable Linux boundary')
    parser = argparse.ArgumentParser(); parser.add_argument('app', choices=VERSIONS); args = parser.parse_args()
    global responses, Event, ToolCall
    sys.path.insert(0, '/pcc')
    from serve import responses
    from serve.frontend import Event, ToolCall
    fixture = Fixture(args.app)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass
        def do_POST(self):
            try:
                length = int(self.headers['Content-Length']); assert 0 < length < 2**20
                body = json.loads(self.rfile.read(length))
                with fixture.lock:
                    raw = fixture.reply(self.path, body)
                self.send_response(200); self.send_header('Content-Type', 'text/event-stream')
                self.send_header('Content-Length', str(len(raw))); self.end_headers(); self.wfile.write(raw)
            except Exception as error:
                fixture.failures.append(dict(type=type(error).__name__, message=str(error)))
                self.send_error(400, 'Fixture contract failed')

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    argv = configuration(args.app, server.server_port)
    started = time.monotonic(); process = None; timed_out = False
    try:
        process = subprocess.run(argv, capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=90)
    except subprocess.TimeoutExpired:
        timed_out = True
    finally:
        server.shutdown(); server.server_close(); thread.join(timeout=2)
    root = Path('/work')
    (root/'requests-private.json').write_text(json.dumps(fixture.requests, indent=2) + '\n')
    (root/'calls-private.json').write_text(json.dumps(fixture.calls, indent=2) + '\n')
    (root/'cli-private.jsonl').write_text(process.stdout if process else '')
    (root/'stderr-private.txt').write_text(process.stderr if process else '')
    repaired = (root/'app.py').read_text() == 'def double(n):\n    return 2*n\n'
    wrote = (root/'notes.txt').is_file() and (root/'notes.txt').read_text() == 'read, write, edit, verify\n'
    passed = bool(process and process.returncode == 0 and not fixture.failures and
                  len(fixture.calls) == 4 and len(fixture.requests) == 5 and repaired and wrote)
    result = dict(schema=2, app=args.app, version=VERSIONS[args.app], passed=passed,
        evidence_kind='synthetic_transport_real_host_tools', real_model_calls=0,
        mock_requests=len(fixture.requests), tool_calls=len(fixture.calls),
        actual_tools=[c['name'] for c in fixture.calls], continuation_results_verified=passed,
        repair_verified=repaired, write_verified=wrote, timed_out=timed_out,
        exit_code=process.returncode if process else None, seconds=time.monotonic()-started,
        failures=fixture.failures, actual_pcc_responses_serializer=args.app == 'codex',
        pcc_native_backend_tested=False, wen_quality_measured=False, weights_updated=False, promoted=False)
    (root/'result.json').write_text(json.dumps(result, indent=2) + '\n'); print(json.dumps(result))
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
