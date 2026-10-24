from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import socket
import tempfile
import threading
import unittest

if os.name == 'posix' and hasattr(socket, 'AF_UNIX'):
    from sss_integration.model_socket import ModelSocket, UnixHTTPConnection, LoopbackRelay


@unittest.skipUnless(os.name == 'posix' and hasattr(socket, 'AF_UNIX'), 'Optional Linux Unix-socket transport')
class ModelSocketTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix='sss-model-')
        self.root = Path(self.directory.name)
        self.seen = []; self.status = 200; self.check_intent = None
        self.payload = b'data: original response\n\ndata: [DONE]\n\n'; self.length_extra = 0
        owner = self

        class Backend(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass
            def do_POST(self):
                raw = self.rfile.read(int(self.headers['Content-Length']))
                owner.seen.append(dict(body=json.loads(raw), authorization=self.headers.get('Authorization')))
                if owner.check_intent:
                    owner.check_intent()
                data = owner.payload
                self.send_response(owner.status);self.send_header('Content-Type','text/event-stream')
                self.send_header('Content-Length',str(len(data)+owner.length_extra));self.end_headers();self.wfile.write(data)

        self.backend = ThreadingHTTPServer(('127.0.0.1',0),Backend)
        self.thread = threading.Thread(target=self.backend.serve_forever,daemon=True);self.thread.start()
        self.key = self.root/'host-key';self.key.write_text('host-fixture-key\n')
        self.endpoint = ModelSocket(self.root/'endpoint',port=self.backend.server_port,model='pinned-model',
            operation_id='original-host-operation',api_key_file=self.key,maximum_calls=2,timeout=3).start()

    def tearDown(self):
        self.endpoint.close();self.backend.shutdown();self.backend.server_close();self.thread.join(timeout=3)
        self.directory.cleanup()

    def request(self, body=None, *, route='/v1/chat/completions'):
        if body is None:
            body=dict(model='pinned-model',messages=[dict(role='user',content='owned task')],stream=True)
        connection=UnixHTTPConnection(self.endpoint.path,timeout=4)
        connection.request('POST',route,json.dumps(body).encode(),headers={'Content-Type':'application/json','Authorization':'Bearer client-value'})
        response=connection.getresponse();status=response.status;raw=response.read();connection.close()
        return status,raw

    def test_intent_precedes_forwarding_and_credentials_stay_at_host(self):
        def check():
            intent=json.loads((self.endpoint.root/'request-1-intent.json').read_text())
            self.assertEqual(intent['operation_id'],'original-host-operation:1')
            self.assertFalse(intent['forwarded'])
        self.check_intent=check
        status,raw=self.request()
        self.assertEqual(status,200);self.assertIn(b'[DONE]',raw)
        self.assertEqual(self.seen[0]['authorization'],'Bearer host-fixture-key')
        self.assertEqual(self.seen[0]['body']['temperature'],0)
        self.assertEqual(self.seen[0]['body']['seed'],0)
        self.assertEqual(self.seen[0]['body']['max_tokens'],512)
        receipt=json.loads((self.endpoint.root/'request-1-receipt.json').read_text())
        self.assertEqual(receipt['outcome'],'complete')
        self.assertNotIn('host-fixture-key',json.dumps(receipt))

    def test_different_model_seed_budget_and_routes_never_reach_backend(self):
        for body,route in [
                (dict(model='other-model'),'/v1/responses'),
                (dict(model='pinned-model',seed=1),'/v1/responses'),
                (dict(model='pinned-model',seed=False),'/v1/responses'),
                (dict(model='pinned-model',max_tokens=513),'/v1/chat/completions'),
                (dict(model='pinned-model'),'/admin')]:
            self.assertEqual(self.request(body,route=route)[0],400)
        self.assertFalse(self.seen);self.assertEqual(self.endpoint.calls,0)

    def test_call_budget_prevents_an_extra_native_operation(self):
        self.assertEqual(self.request()[0],200);self.assertEqual(self.request()[0],200)
        self.assertEqual(self.request()[0],400)
        self.assertEqual(len(self.seen),2)

    def test_upstream_error_stops_all_further_forwarding(self):
        self.status=503
        self.assertEqual(self.request()[0],503);self.status=200
        self.assertEqual(self.request()[0],400)
        self.assertEqual(len(self.seen),1);self.assertTrue(self.endpoint.stopped)
        self.assertEqual(self.endpoint.records[0]['outcome'],'infrastructure_error')

    def test_lost_response_is_uncertain_and_never_retried(self):
        self.endpoint.maximum_response_bytes=1
        self.assertEqual(self.request()[0],200)
        self.assertEqual(self.request()[0],400)
        self.assertEqual(len(self.seen),1)
        self.assertEqual(self.endpoint.records[0]['outcome'],'uncertain')

    def test_eof_without_api_terminal_is_uncertain(self):
        self.payload=b'data: {"choices": []}\n\n'
        self.assertEqual(self.request()[0],200)
        self.assertEqual(self.endpoint.records[0]['outcome'],'uncertain')
        self.assertEqual(self.request()[0],400);self.assertEqual(len(self.seen),1)

    def test_explicit_stream_error_is_infrastructure_failure(self):
        self.payload=b'event: error\ndata: {"type": "error", "error": {"message": "owned fixture failure"}}\n\n'
        self.assertEqual(self.request()[0],200)
        self.assertEqual(self.endpoint.records[0]['outcome'],'infrastructure_error')
        self.assertEqual(self.request()[0],400);self.assertEqual(len(self.seen),1)

    def test_declared_length_truncation_is_uncertain_even_after_done(self):
        self.length_extra=10
        self.assertEqual(self.request()[0],200)
        self.assertEqual(self.endpoint.records[0]['outcome'],'uncertain')
        self.assertEqual(self.request()[0],400);self.assertEqual(len(self.seen),1)

    def test_loopback_relay_streams_before_upstream_finishes(self):
        first=threading.Event();release=threading.Event()
        opening=b'data: first\n\n';ending=b'data: [DONE]\n\n'
        class StreamingBackend(BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_POST(self):
                self.rfile.read(int(self.headers['Content-Length']))
                self.send_response(200);self.send_header('Content-Length',str(len(opening)+len(ending)));self.end_headers()
                self.wfile.write(opening);self.wfile.flush();first.set()
                if not release.wait(3):return
                self.wfile.write(ending);self.wfile.flush()
        server=ThreadingHTTPServer(('127.0.0.1',0),StreamingBackend)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        self.endpoint.port=server.server_port
        relay=LoopbackRelay(self.endpoint.path,timeout=4).start()
        from http.client import HTTPConnection
        connection=HTTPConnection('127.0.0.1',relay.port,timeout=4)
        try:
            connection.request('POST','/v1/responses',json.dumps(dict(model='pinned-model',stream=True)).encode())
            response=connection.getresponse();self.assertTrue(first.wait(1))
            self.assertEqual(response.read(len(opening)),opening);release.set()
            self.assertEqual(response.read(),ending)
        finally:
            release.set();connection.close();relay.close();server.shutdown();server.server_close();thread.join(timeout=3)


if __name__=='__main__':
    unittest.main()
