"""Exercise installed applications with a deterministic local protocol fixture.
Run INSIDE the prepared Linux namespace. This is not model inference or mastery.
"""
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import argparse,json,os,subprocess,threading,time,signal

COMMANDS=["cat app.py", "printf 'read, write, edit, verify\n' > notes.txt", "python3 -c \"from pathlib import Path;p=Path('app.py');p.write_text(p.read_text().replace('return n','return 2*n'))\"", "python3 -c 'import app; assert app.double(21)==42; print(\"checked\")'"]
PROMPT='Read app.py. Write notes.txt describing the steps. Repair double(n) to return twice n, verify it, then report completion. Work only in this prepared project.'

class Fixture:
    def __init__(self):self.step=0;self.requests=[];self.tool_names=[]
    def respond(self,request):
        self.requests.append(request)
        tools=request.get('tools',[]);functions=[t.get('function',t) for t in tools]
        names={f.get('name'):f for f in functions}
        if not names:return 'S3 fixture',None
        if self.step>=len(COMMANDS):return 'Completed the repair and verification.',None
        name=next((n for n in ('exec_command','bash','shell_command','shell') if n in names),None)
        if not name:raise ValueError('Application advertised no supported shell tool: '+','.join(str(n) for n in names))
        spec=names[name].get('parameters') or names[name].get('input_schema') or {};props=spec.get('properties',{})
        args={}
        if 'cmd' in props:args['cmd']=COMMANDS[self.step]
        elif 'command' in props:args['command']=COMMANDS[self.step]
        elif 'commands' in props:args['commands']=[COMMANDS[self.step]]
        else:raise ValueError('Unrecognized native shell schema: '+json.dumps(spec))
        if 'description' in props:args['description']='Owned S3 protocol fixture step'
        if 'workdir' in props:args['workdir']='/work'
        for key in spec.get('required',[]):
            if key not in args:raise ValueError('Unrecognized required tool argument '+key)
        call=dict(id='call_'+str(self.step),name=name,arguments=json.dumps(args));self.step+=1;self.tool_names.append(name)
        return '',call

def serve(fixture):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_GET(self):
            raw=json.dumps(dict(object='list',data=[dict(id='sss-reference',object='model',owned_by='fixture')])).encode()
            self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
        def do_POST(self):
            request=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            try:text,call=fixture.respond(request)
            except Exception as error:
                raw=json.dumps(dict(error=dict(message=str(error)))).encode();self.send_response(400);self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw);return
            response_id='resp_'+str(len(fixture.requests));created=int(time.time());usage=dict(input_tokens=20,output_tokens=10,total_tokens=30)
            is_responses=self.path.endswith('/responses')
            message=dict(role='assistant',content=text)
            if call:message['tool_calls']=[dict(id=call['id'],type='function',function=dict(name=call['name'],arguments=call['arguments']))]
            item=(dict(id='fc_'+call['id'],type='function_call',call_id=call['id'],name=call['name'],arguments=call['arguments'],status='completed') if call else dict(id='msg_'+response_id,type='message',role='assistant',status='completed',content=[dict(type='output_text',text=text,annotations=[])]))
            response=dict(id=response_id,object='response',created_at=created,status='completed',model='sss-reference',output=[item],usage=usage)
            if not request.get('stream'):
                body=response if is_responses else dict(id=response_id,object='chat.completion',created=created,model='sss-reference',choices=[dict(index=0,message=message,finish_reason='tool_calls' if call else 'stop')],usage=dict(prompt_tokens=20,completion_tokens=10,total_tokens=30))
                raw=json.dumps(body).encode();self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw);return
            self.send_response(200);self.send_header('Content-Type','text/event-stream');self.send_header('Connection','close');self.end_headers();self.close_connection=True
            def emit(value,event=None):
                prefix=('event: '+event+'\n') if event else ''
                self.wfile.write((prefix+'data: '+json.dumps(value)+'\n\n').encode());self.wfile.flush()
            if is_responses:
                seq=0
                def event(kind,**data):
                    nonlocal seq
                    emit(dict(type=kind,sequence_number=seq,**data),kind);seq+=1
                event('response.created',response=dict(response,status='in_progress',output=[]))
                event('response.in_progress',response=dict(response,status='in_progress',output=[]))
                initial=dict(item,status='in_progress')
                if call:initial['arguments']=''
                else:initial['content']=[]
                event('response.output_item.added',output_index=0,item=initial)
                if call:
                    event('response.function_call_arguments.delta',output_index=0,item_id=item['id'],delta=call['arguments'])
                    event('response.function_call_arguments.done',output_index=0,item_id=item['id'],arguments=call['arguments'])
                else:
                    part=dict(type='output_text',text='',annotations=[])
                    event('response.content_part.added',output_index=0,item_id=item['id'],content_index=0,part=part)
                    event('response.output_text.delta',output_index=0,item_id=item['id'],content_index=0,delta=text)
                    event('response.output_text.done',output_index=0,item_id=item['id'],content_index=0,text=text)
                    event('response.content_part.done',output_index=0,item_id=item['id'],content_index=0,part=dict(part,text=text))
                event('response.output_item.done',output_index=0,item=item);event('response.completed',response=response)
            else:
                base=dict(id=response_id,object='chat.completion.chunk',created=created,model='sss-reference')
                delta=dict(message)
                if call:delta['tool_calls'][0]['index']=0
                emit(dict(base,choices=[dict(index=0,delta=delta,finish_reason=None)]))
                emit(dict(base,choices=[dict(index=0,delta={},finish_reason='tool_calls' if call else 'stop')],usage=dict(prompt_tokens=20,completion_tokens=10,total_tokens=30)))
                self.wfile.write(b'data: [DONE]\n\n');self.wfile.flush()
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler);threading.Thread(target=server.serve_forever,daemon=True).start();return server

def main():
    p=argparse.ArgumentParser();p.add_argument('app',choices=['codex','opencode','pi']);args=p.parse_args()
    fixture=Fixture();server=serve(fixture);base='http://127.0.0.1:'+str(server.server_port)+'/v1'
    home=Path('/tmp/app-home');home.mkdir();env=dict(os.environ,HOME=str(home),XDG_CONFIG_HOME=str(home/'config'),XDG_DATA_HOME=str(home/'data'),XDG_CACHE_HOME=str(home/'cache'),PATH='/usr/bin:/bin:/apps/node_modules/.bin')
    executable='/apps/node_modules/.bin/'+args.app
    if args.app=='codex':
        codex_home=home/'codex';codex_home.mkdir();env['CODEX_HOME']=str(codex_home)
        (codex_home/'config.toml').write_text('model="sss-reference"\nmodel_provider="sss"\n[model_providers.sss]\nname="S3 protocol fixture"\nbase_url='+json.dumps(base)+'\nwire_api="responses"\nrequires_openai_auth=false\n')
        cmd=[executable,'exec','--json','--ephemeral','--skip-git-repo-check','--dangerously-bypass-approvals-and-sandbox','-C','/work',PROMPT]
    elif args.app=='opencode':
        env['OPENCODE_CONFIG_CONTENT']=json.dumps(dict(provider=dict(sss=dict(npm='@ai-sdk/openai-compatible',name='S3 fixture',options=dict(baseURL=base,apiKey='fixture'),models={'sss-reference':dict(name='S3 reference',limit=dict(context=131072,output=2048))})),model='sss/sss-reference',permission='allow',share='disabled',autoupdate=False))
        env['OPENCODE_DISABLE_DEFAULT_PLUGINS']='true';env['OPENCODE_DISABLE_MODELS_FETCH']='true'
        cmd=[executable,'run','--pure','--auto','--format','json','--title','S3 fixture','--dir','/work','-m','sss/sss-reference',PROMPT]
    else:
        agent=home/'pi';agent.mkdir();env['PI_CODING_AGENT_DIR']=str(agent)
        (agent/'models.json').write_text(json.dumps(dict(providers=dict(sss=dict(baseUrl=base,api='openai-completions',apiKey='fixture',models=[dict(id='sss-reference',name='S3 reference',reasoning=False,input=['text'],contextWindow=131072,maxTokens=2048)])))))
        cmd=[executable,'--mode','rpc','--no-session','--no-extensions','--no-mcp','--no-skills','--no-prompt-templates','--no-context-files','--no-approve','--provider','sss','--model','sss-reference','--thinking','off']
    events=[]
    with Path('/work/application.stderr').open('wb') as stderr:
        proc=subprocess.Popen(cmd,cwd='/work',env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=stderr)
        if args.app=='pi':proc.stdin.write((json.dumps(dict(id='sss-prompt',type='prompt',message=PROMPT))+'\n').encode());proc.stdin.flush()
        else:proc.stdin.close()
        def collect():
            for raw in proc.stdout:
                # Binary LF framing preserves U+2028/U+2029 inside JSON strings.
                line=raw.decode('utf-8',errors='replace').rstrip('\r\n');events.append(line)
                if args.app=='pi':
                    try:event=json.loads(line)
                    except ValueError:continue
                    if event.get('type')=='agent_settled':proc.stdin.close()
        reader=threading.Thread(target=collect,daemon=True);reader.start()
        try:proc.wait(timeout=80)
        except subprocess.TimeoutExpired:proc.kill();proc.wait()
        reader.join(timeout=3)
    server.shutdown();server.server_close()
    Path('/work/application.events.jsonl').write_text('\n'.join(events)+'\n')
    Path('/work/protocol-private.json').write_text(json.dumps(dict(requests=fixture.requests,tool_names=fixture.tool_names)))
    result=dict(app=args.app,exit_code=proc.returncode,calls=fixture.step,model_inference=False,weights_updated=False)
    print(json.dumps(result));return 0 if proc.returncode==0 and fixture.step==4 else 1

if __name__=='__main__':raise SystemExit(main())
