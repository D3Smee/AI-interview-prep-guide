#!/usr/bin/env python3
"""
Local proxy for Interview Prep tool.
Forwards /api/messages requests to Anthropic, adding CORS headers so
normal Chrome (no flags) can call the API without a security error.

Usage:
  python3 proxy.py
Then open http://localhost:3000 in Chrome.
"""
import json
import os
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

PORT = 3000
HTML_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Interview prep.html')


class ProxyHandler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        print(f"  {self.command} {self.path} → {fmt % args}")

    # ── CORS preflight ────────────────────────────────────────────────
    def do_OPTIONS(self):
        self.send_response(204)
        self._cors_headers()
        self.end_headers()

    # ── Serve the HTML app ────────────────────────────────────────────
    def do_GET(self):
        if self.path.rstrip('/') in ('', '/index.html', '/Interview%20prep.html'):
            try:
                with open(HTML_FILE, 'rb') as f:
                    body = f.read()
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Content-Length', str(len(body)))
                self._cors_headers()
                self.end_headers()
                self.wfile.write(body)
            except FileNotFoundError:
                self.send_error(404, f'HTML file not found: {HTML_FILE}')
        else:
            self.send_error(404, 'Not found')

    # ── Proxy API calls ───────────────────────────────────────────────
    def do_POST(self):
        if self.path != '/api/messages':
            self.send_error(404, 'Not found')
            return

        length = int(self.headers.get('Content-Length', 0))
        raw = self.rfile.read(length)

        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            self.send_error(400, 'Invalid JSON body')
            return

        api_key = payload.pop('apiKey', '').strip()
        if not api_key:
            self._json_error(400, 'Missing apiKey in request body')
            return

        upstream_body = json.dumps(payload).encode()
        req = urllib.request.Request(
            'https://api.anthropic.com/v1/messages',
            data=upstream_body,
            headers={
                'Content-Type': 'application/json',
                'x-api-key': api_key,
                'anthropic-version': '2023-06-01',
            },
            method='POST',
        )

        try:
            with urllib.request.urlopen(req) as resp:
                self.send_response(resp.status)
                # Forward upstream headers, skip hop-by-hop ones
                skip = {'transfer-encoding', 'connection', 'keep-alive'}
                for k, v in resp.headers.items():
                    if k.lower() not in skip:
                        self.send_header(k, v)
                self._cors_headers()
                self.end_headers()
                # Stream chunks straight through
                while True:
                    chunk = resp.read(4096)
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    self.wfile.flush()

        except urllib.error.HTTPError as e:
            body = e.read()
            self.send_response(e.code)
            self.send_header('Content-Type', 'application/json')
            self._cors_headers()
            self.end_headers()
            self.wfile.write(body)

    # ── Helpers ───────────────────────────────────────────────────────
    def _cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def _json_error(self, code, message):
        body = json.dumps({'error': {'message': message}}).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self._cors_headers()
        self.end_headers()
        self.wfile.write(body)


if __name__ == '__main__':
    server = HTTPServer(('localhost', PORT), ProxyHandler)
    print(f'Proxy running → http://localhost:{PORT}')
    print(f'Serving:        {HTML_FILE}')
    print('Press Ctrl+C to stop.\n')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nStopped.')
