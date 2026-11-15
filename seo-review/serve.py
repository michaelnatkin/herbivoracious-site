import http.server,json,os
D=os.path.dirname(os.path.abspath(__file__));F=os.path.join(D,"decisions.json")
class H(http.server.SimpleHTTPRequestHandler):
    def __init__(s,*a,**k):super().__init__(*a,directory=D,**k)
    def do_GET(s):
        if s.path.startswith("/decisions.json") and not os.path.exists(F):
            s.send_response(200);s.end_headers();s.wfile.write(b"{}");return
        super().do_GET()
    def do_POST(s):
        b=json.loads(s.rfile.read(int(s.headers.get("Content-Length",0))))
        e=json.load(open(F)) if os.path.exists(F) else {}
        e.update(b);json.dump(e,open(F,"w"),indent=1);s.send_response(200);s.end_headers();s.wfile.write(b"ok")
    def end_headers(s):s.send_header("Cache-Control","no-store");super().end_headers()
    def log_message(s,*a):pass
http.server.ThreadingHTTPServer(("127.0.0.1",8124),H).serve_forever()
