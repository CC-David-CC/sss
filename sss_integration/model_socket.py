"""Bounded test transport: isolated client -> Unix socket -> fixed model port.

No workflow, tool authority, model fallback or automatic retries live here.
The host retains credentials and records intent before forwarding each request.
"""
from http.client import HTTPConnection
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import hashlib
import json
import os
from pathlib import Path
import socket
from socketserver import UnixStreamServer
import threading
import time


ROUTES = {'/v1/responses', '/v1/chat/completions'}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def write_new(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2); stream.write('\n'); stream.flush(); os.fsync(stream.fileno())


class UnixHTTPConnection(HTTPConnection):
    def __init__(self, path, *, timeout=90):
        super().__init__('localhost', timeout=timeout)
        self.socket_path = str(path)

    def connect(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.settimeout(self.timeout)
        self.sock.connect(self.socket_path)


class ModelSocket:
    """One owned endpoint for one bounded host operation, not a shared service."""
    def __init__(self, root, *, port, model, operation_id, api_key_file=None,
                 maximum_calls=12, output_bound=512, timeout=90,
                 maximum_body_bytes=1048576, maximum_response_bytes=8388608):
        if not (type(port) is int and 0 < port < 65536 and type(maximum_calls) is int and 0 < maximum_calls <= 128
                and type(output_bound) is int and 0 < output_bound <= 32768 and 0 < timeout <= 180):
            raise ValueError('Explicit bounded local endpoint required')
        if not model or not operation_id or any(c in model+operation_id for c in '\r\n\0'):
            raise ValueError('Explicit model and original operation identity required')
        if (type(maximum_body_bytes) is not int or not 0 < maximum_body_bytes <= 16*1024**2
                or type(maximum_response_bytes) is not int or not 0 < maximum_response_bytes <= 64*1024**2):
            raise ValueError('Bounded request/response sizes required')
        self.root = Path(root).absolute()
        if len(os.fsencode(str(self.root/'model.sock'))) >= 104:
            raise ValueError('Use a short owned endpoint path within the Unix socket limit')
        self.root.mkdir(mode=0o700, parents=True, exist_ok=False)
        if self.root.stat().st_uid != os.getuid():
            raise ValueError('Owned private endpoint directory required')
        self.path = self.root/'model.sock'
        self.port, self.model, self.operation_id = port, model, operation_id
        self.key = Path(api_key_file).read_text().strip() if api_key_file else None
        self.maximum_calls, self.output_bound, self.timeout = maximum_calls, output_bound, timeout
        self.maximum_body_bytes, self.maximum_response_bytes = maximum_body_bytes, maximum_response_bytes
        self.calls = 0; self.requests = 0; self.stopped = False; self.records = []
        self.server = None; self.thread = None

    def start(self):
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def setup(self):
                super().setup(); self.connection.settimeout(owner.timeout)

            def do_GET(self):
                self.handle_request('GET')

            def do_POST(self):
                self.handle_request('POST')

            def handle_request(self, method):
                owner.requests += 1
                number = owner.requests
                operation = owner.operation_id + ':' + str(number)
                stem = owner.root/('request-' + str(number))
                started = time.monotonic()
                connection = None; response_started = False; forwarded = False
                record = dict(operation_id=operation, method=method, path=self.path, outcome='rejected', forwarded=False)
                try:
                    if owner.requests > owner.maximum_calls+8 or owner.stopped:
                        raise ValueError('Endpoint stopped; reconcile original operations before any retry')
                    if self.path not in ROUTES and not (method == 'GET' and self.path == '/v1/models'):
                        raise ValueError('Route outside the model endpoint grant')
                    if method == 'GET' and self.path != '/v1/models':
                        raise ValueError('GET is only supported for model discovery')
                    if method == 'POST':
                        if self.headers.get('Transfer-Encoding'):
                            raise ValueError('Explicit bounded Content-Length required')
                        length = int(self.headers.get('Content-Length', '-1'))
                        if not 0 < length <= owner.maximum_body_bytes:
                            raise ValueError('Request body exceeds the declared bound')
                        original = self.rfile.read(length)
                        if len(original) != length:
                            raise ValueError('Incomplete original request')
                        body = json.loads(original)
                        if type(body) is not dict or body.get('model') != owner.model:
                            raise ValueError('Model differs from the pinned endpoint')
                        if body.get('stream') is not True:
                            raise ValueError('Only explicitly streaming client requests are qualified')
                        temperature, seed = body.get('temperature', 0), body.get('seed', 0)
                        if type(temperature) not in (int, float) or temperature != 0 or type(seed) is not int or seed != 0:
                            raise ValueError('Sampling differs from the declared fixed policy')
                        field = 'max_output_tokens' if self.path.endswith('/responses') else 'max_tokens'
                        limit = body.get('max_completion_tokens', body.get(field, owner.output_bound))
                        if type(limit) is not int or not 0 < limit <= owner.output_bound:
                            raise ValueError('Output allowance differs from the bounded policy')
                        if owner.calls >= owner.maximum_calls:
                            raise ValueError('Model-call budget exhausted')
                        body.setdefault('temperature', 0); body.setdefault('seed', 0)
                        body.setdefault(field, owner.output_bound)
                        sent = json.dumps(body, separators=(',', ':')).encode()
                        with Path(str(stem)+'-original-private.json').open('xb') as out:
                            out.write(original); out.flush(); os.fsync(out.fileno())
                        with Path(str(stem)+'-sent-private.json').open('xb') as out:
                            out.write(sent); out.flush(); os.fsync(out.fileno())
                        record.update(original_sha256=sha(original), sent_sha256=sha(sent),
                            sampling=dict(temperature=body['temperature'], seed=body['seed']), output_bound=limit,
                            normalization='Fill omitted temperature=0, seed=0 and output bound; preserve other request fields')
                    else:
                        sent = None
                    # This immutable intent precedes any upstream operation.
                    write_new(str(stem)+'-intent.json', record)
                    headers = {'Content-Type': 'application/json'}
                    if owner.key:
                        headers['Authorization'] = 'Bearer ' + owner.key
                    connection = HTTPConnection('127.0.0.1', owner.port, timeout=owner.timeout)
                    if method == 'POST':
                        owner.calls += 1
                    forwarded = True
                    connection.request(method, self.path, body=sent, headers=headers)
                    response = connection.getresponse()
                    record.update(forwarded=True, upstream_status=response.status)
                    self.send_response(response.status)
                    self.send_header('Content-Type', response.getheader('Content-Type', 'application/json'))
                    self.send_header('Connection', 'close'); self.end_headers(); response_started = True
                    size = 0; digest = hashlib.sha256(); pending = b''; terminal = False; protocol_failed = False
                    with Path(str(stem)+'-response-private.bin').open('xb') as out:
                        while True:
                            chunk = response.read1(65536)
                            if not chunk:
                                break
                            size += len(chunk)
                            if size > owner.maximum_response_bytes:
                                raise ValueError('Upstream response exceeds the declared bound')
                            out.write(chunk); digest.update(chunk); self.wfile.write(chunk); self.wfile.flush()
                            pending += chunk
                            while b'\n' in pending:
                                line, pending = pending.split(b'\n',1)
                                if not line.startswith(b'data:'):
                                    continue
                                payload = line[5:].strip()
                                if payload == b'[DONE]':
                                    terminal = True
                                else:
                                    try:
                                        event = json.loads(payload)
                                    except ValueError:
                                        continue
                                    if type(event) is dict and event.get('type') in ('response.completed','response.incomplete','response.failed','error'):
                                        terminal = True
                                    if type(event) is dict and (event.get('type') in ('response.failed','error') or 'error' in event):
                                        protocol_failed = True
                    length = response.getheader('Content-Length')
                    if length is not None and size != int(length):
                        raise ValueError('Upstream response ended before its declared length')
                    if method == 'POST' and response.status < 400 and not terminal:
                        raise ValueError('Stream ended without an API terminal event')
                    record.update(response_bytes=size, response_sha256=digest.hexdigest(),
                        terminal_event=terminal, outcome='complete' if response.status < 400 and not protocol_failed else 'infrastructure_error')
                    if response.status >= 400 or protocol_failed:
                        owner.stopped = True
                except Exception as error:
                    record.update(forwarded=forwarded, outcome='uncertain' if forwarded else 'rejected',
                                  error_type=type(error).__name__, error=str(error))
                    if forwarded:
                        owner.stopped = True
                    if not response_started:
                        self.send_error(502 if forwarded else 400, 'Model transport refused; inspect original receipt')
                finally:
                    if connection:
                        connection.close()
                    self.close_connection = True
                    record['elapsed_seconds'] = time.monotonic()-started
                    owner.records.append(record)
                    write_new(str(stem)+'-receipt.json', record)

        self.server = UnixStreamServer(str(self.path), Handler)
        self.path.chmod(0o600); self.inode = self.path.stat().st_ino
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        return self

    def close(self):
        if self.server:
            self.server.shutdown(); self.server.server_close(); self.thread.join(timeout=self.timeout+2)
            if self.thread.is_alive():
                raise RuntimeError('Original model transport did not settle')
            if self.path.exists() and self.path.stat().st_ino == self.inode:
                self.path.unlink()
        write_new(self.root/'settlement.json', dict(settled=True, model_calls=self.calls,
            requests=self.requests, stopped=self.stopped, operations=[r['operation_id'] for r in self.records],
            uncertain=any(r['outcome']=='uncertain' for r in self.records)))


class LoopbackRelay:
    """Client-side HTTP socket inside the isolated namespace; no credentials."""
    def __init__(self, socket_path, *, timeout=90):
        self.socket_path, self.timeout = str(socket_path), timeout

    def start(self):
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass
            def do_POST(self):
                self.forward('POST')
            def do_GET(self):
                self.forward('GET')
            def forward(self, method):
                connection = UnixHTTPConnection(owner.socket_path, timeout=owner.timeout)
                try:
                    body = None
                    if method == 'POST':
                        length = int(self.headers.get('Content-Length', '-1'))
                        if not 0 < length <= 1048576 or self.headers.get('Transfer-Encoding'):
                            self.send_error(400); return
                        body = self.rfile.read(length)
                    connection.request(method, self.path, body=body, headers={'Content-Type':'application/json'})
                    response = connection.getresponse()
                    self.send_response(response.status)
                    self.send_header('Content-Type',response.getheader('Content-Type','application/json'))
                    self.send_header('Connection','close'); self.end_headers()
                    while True:
                        chunk = response.read1(65536)
                        if not chunk:
                            break
                        self.wfile.write(chunk); self.wfile.flush()
                finally:
                    self.close_connection = True; connection.close()

        self.server = ThreadingHTTPServer(('127.0.0.1',0),Handler)
        self.thread = threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.port = self.server.server_port
        return self

    def close(self):
        self.server.shutdown();self.server.server_close();self.thread.join(timeout=2)
