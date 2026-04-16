"""
The Squirrel — HTTP server on port 8425.
GET  /         → rendered Squirrel.md as HTML
GET  /mtime    → {"mtime": float}
POST /write    → append {"text": str} to Squirrel.md
GET  /skins/*  → serve from skins/
"""
# Bootstrap WILLOW_CORE before any db.* import fires.
import os as _os, sys as _sys
if not _os.environ.get("WILLOW_CORE"):
    from pathlib import Path as _P
    _fake = _P.home() / ".squirrel" / "willow_core"
    _fake.mkdir(parents=True, exist_ok=True)
    (_fake / "user_lattice.py").write_text(
        "DOMAINS=frozenset({'biography','geography','genealogy','culture','migration'})\n"
        "TEMPORAL_STATES=frozenset({'past','present','future','unknown'})\n"
        "DEPTH_MIN=1;DEPTH_MAX=23;LATTICE_SIZE=23\n"
    )
    _os.environ["WILLOW_CORE"] = str(_fake)
_os.environ.setdefault("SAP_AUTHORIZED", "1")

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse

import markdown as _md

PORT = 8425
SQUIRREL_MD = Path("Squirrel.md")
SKINS_DIR = Path(__file__).parent / "skins"

WELCOME_BLOCK = """# The Squirrel
*genealogy research terminal — the file is the interface*

**Commands:**
- `@squirrel: add person Oscar Mann b.1882 d.1951 p.Iowa`
- `@squirrel: tree Oscar Mann`
- `@squirrel: show people`
- `@squirrel: find sources Iowa 1880s`
- `@squirrel: mode listening` — invite the LLM in
- `@squirrel: status`
- `@squirrel: skin 80s`

---
"""

_file_lock = threading.RLock()


def ensure_squirrel_md(path: Path = SQUIRREL_MD):
    if not path.exists():
        path.write_text(WELCOME_BLOCK, encoding="utf-8")


def _render_html(skin: str = "mcm") -> str:
    ensure_squirrel_md()
    raw = SQUIRREL_MD.read_text(encoding="utf-8")
    body = _md.markdown(raw, extensions=["fenced_code", "tables"])
    return f"""<!DOCTYPE html>
<html lang="en" data-skin="{skin}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>The Squirrel</title>
<link rel="stylesheet" href="/skins/base.css">
<link rel="stylesheet" href="/skins/{skin}.css">
</head>
<body>
<div id="header">
  <div id="title">THE SQUIRREL</div>
  <div id="mode-toggle">
    <label>Journal</label>
    <input type="range" min="0" max="2" value="0" id="mode-slider" oninput="setMode(this.value)">
    <label>Chat</label>
  </div>
</div>
<div id="content">{body}</div>
<div id="input-area">
  <textarea id="cmd" placeholder="@squirrel: ..." rows="2"></textarea>
  <button onclick="submitCmd()">&crarr;</button>
</div>
<script>
const MODES = ["journal","listening","chat"];
function setMode(v) {{
  fetch("/write", {{method:"POST",headers:{{"Content-Type":"application/json"}},
    body:JSON.stringify({{text:"@squirrel: mode "+MODES[v]}})}});
}}
function submitCmd() {{
  const t = document.getElementById("cmd").value.trim();
  if (!t) return;
  fetch("/write", {{method:"POST",headers:{{"Content-Type":"application/json"}},
    body:JSON.stringify({{text:t}})}})
  .then(() => {{ document.getElementById("cmd").value = ""; }});
}}
document.getElementById("cmd").addEventListener("keydown", e => {{
  if (e.key === "Enter" && !e.shiftKey) {{ e.preventDefault(); submitCmd(); }}
}});
let _mtime = 0;
setInterval(async () => {{
  const r = await fetch("/mtime");
  const d = await r.json();
  if (d.mtime !== _mtime) {{ _mtime = d.mtime; location.reload(); }}
}}, 1500);
</script>
</body>
</html>"""


class SquirrelHandler(BaseHTTPRequestHandler):
    skin = "mcm"

    def log_message(self, fmt, *args):
        pass

    def do_GET(self):
        p = urlparse(self.path)
        if p.path == "/":
            html = _render_html(self.skin).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", len(html))
            self.end_headers()
            self.wfile.write(html)
        elif p.path == "/mtime":
            mtime = SQUIRREL_MD.stat().st_mtime if SQUIRREL_MD.exists() else 0
            body = json.dumps({"mtime": mtime}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body)
        elif p.path.startswith("/skins/"):
            fname = p.path[len("/skins/"):]
            css_path = SKINS_DIR / fname
            if css_path.exists() and css_path.suffix == ".css":
                data = css_path.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "text/css")
                self.end_headers()
                self.wfile.write(data)
            else:
                self.send_response(404); self.end_headers()
        else:
            self.send_response(404); self.end_headers()

    def do_POST(self):
        if self.path == "/write":
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length))
            text = body.get("text", "").strip()
            if text:
                with _file_lock:
                    with open(SQUIRREL_MD, "a", encoding="utf-8") as f:
                        f.write("\n" + text + "\n")
            self.send_response(200); self.end_headers()
        else:
            self.send_response(404); self.end_headers()


def run(port: int = PORT):
    from squirrel_watcher import start_watcher
    from squirrel_responder import make_responder
    from responder.state import AppState
    ensure_squirrel_md()
    state = AppState(squirrel_md=SQUIRREL_MD)
    state.load_config()
    SquirrelHandler.skin = state.skin
    responder_cb = make_responder(state)
    watcher = start_watcher(SQUIRREL_MD, responder_cb, lambda: state.mode.value)
    try:
        server = HTTPServer(("127.0.0.1", port), SquirrelHandler)
        print(f"The Squirrel is open at http://localhost:{port}")
        server.serve_forever()
    finally:
        watcher.stop()
        watcher.join()


if __name__ == "__main__":
    run()

