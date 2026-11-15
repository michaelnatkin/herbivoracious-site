"""Tiny local server for the link review page. Saves decisions to decisions.json.
Run: python3 serve.py   then open http://localhost:8123/"""
import http.server, json, os
import auto_approve

DIR = os.path.dirname(os.path.abspath(__file__))
DEC = os.path.join(DIR, "decisions.json")

class H(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k): super().__init__(*a, directory=DIR, **k)
    def do_GET(self):
        if self.path.startswith("/batches.json"):
            try: auto_approve.run()    # standing rule: high confidence + page loads
            except Exception: pass
            names = sorted(f for f in os.listdir(os.path.join(DIR, "batches")) if f.startswith("batch-") and f.endswith(".json"))
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
            self.wfile.write(json.dumps(names).encode()); return
        if self.path.startswith("/decisions.json") and not os.path.exists(DEC):
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers(); self.wfile.write(b"{}"); return
        super().do_GET()
    def do_POST(self):
        if self.path != "/save": self.send_error(404); return
        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        incoming = json.loads(body)  # validate
        existing = json.load(open(DEC)) if os.path.exists(DEC) else {}
        existing.update(incoming)   # merge: entries added elsewhere (auto-approvals) survive
        json.dump(existing, open(DEC, "w"), indent=1)
        self.send_response(200); self.end_headers(); self.wfile.write(b"ok")
    def end_headers(self):
        self.send_header("Cache-Control", "no-store"); super().end_headers()
    def log_message(self, *a): pass

if __name__ == "__main__":
    http.server.ThreadingHTTPServer(("127.0.0.1", 8123), H).serve_forever()
