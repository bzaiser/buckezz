import os
import sys
import time
import socket
import shutil
import threading
import traceback
import urllib.request
import webbrowser
from pathlib import Path
from socketserver import ThreadingMixIn
from wsgiref.simple_server import WSGIServer, WSGIRequestHandler

# 1. Base environment configuration
if not os.environ.get('SECRET_KEY'):
    os.environ['SECRET_KEY'] = 'django-insecure-desktop-mode-buckezz-key-local-run'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'buckezz_project.settings')

# 2. Per-user database path in LocalAppData
USER_DATA_DIR = Path(os.getenv('LOCALAPPDATA', str(Path.home()))) / 'Buckezz Desktop'
USER_DB_PATH = USER_DATA_DIR / 'db.sqlite3'
LOG_FILE = USER_DATA_DIR / 'buckezz.log'

os.environ['DB_PATH'] = str(USER_DB_PATH)

def _log(msg):
    try:
        USER_DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(f"[{time.strftime('%H:%M:%S')}] {msg}\n")
    except Exception:
        pass

def ensure_user_database():
    """
    Stellt sicher, dass im Benutzerverzeichnis eine valide Datenbank liegt.
    Falls sie nicht existiert oder 0 Bytes hat (z. B. durch Abbruch),
    wird clean_template.sqlite3 hineinkopiert.
    """
    USER_DATA_DIR.mkdir(parents=True, exist_ok=True)
    needs_copy = False
    if not USER_DB_PATH.exists():
        _log(f"DB does not exist at {USER_DB_PATH}, will copy template")
        needs_copy = True
    elif USER_DB_PATH.stat().st_size == 0:
        _log(f"DB at {USER_DB_PATH} is 0 bytes (corrupt), will replace with template")
        needs_copy = True

    if needs_copy:
        # Template suchen
        template_candidates = []
        if getattr(sys, 'frozen', False):
            base_dir = Path(sys.executable).resolve().parent
            bundle_dir = Path(getattr(sys, '_MEIPASS', base_dir / '_internal'))
            template_candidates.extend([
                bundle_dir / 'clean_template.sqlite3',
                base_dir / 'clean_template.sqlite3',
                base_dir / 'db.sqlite3',
            ])
        else:
            base_dir = Path(__file__).resolve().parent
            template_candidates.append(base_dir / 'clean_template.sqlite3')

        copied = False
        for cand in template_candidates:
            if cand.exists() and cand.stat().st_size > 0:
                try:
                    shutil.copy2(cand, USER_DB_PATH)
                    _log(f"Copied DB template from {cand} to {USER_DB_PATH} ({cand.stat().st_size} bytes)")
                    copied = True
                    break
                except Exception:
                    _log(f"Failed to copy from {cand}:\n{traceback.format_exc()}")
        if not copied:
            _log("WARNING: No valid clean_template.sqlite3 found, fallback to empty DB (migrations will create schema)")

ensure_user_database()

import django
django.setup()
_log(f"django.setup: OK (DB={USER_DB_PATH})")

from buckezz_project.wsgi import application
from django.conf import settings
from django.core.management import call_command

class ThreadedWSGIServer(ThreadingMixIn, WSGIServer):
    daemon_threads = True

class SilentHandler(WSGIRequestHandler):
    def log_message(self, format, *args):
        pass

SPLASH_HTML = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {
    margin: 0;
    background: #0f172a;
    color: #f8fafc;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    display: flex;
    align-items: center;
    justify-content: center;
    height: 100vh;
    overflow: hidden;
    user-select: none;
  }
  .box {
    text-align: center;
    width: 480px;
    max-width: 90%;
  }
  .logo-icon {
    font-size: 42px;
    margin-bottom: 12px;
  }
  .title {
    font-size: 24px;
    font-weight: 700;
    margin-bottom: 6px;
    color: #818cf8;
  }
  #status {
    font-size: 13px;
    color: #94a3b8;
    margin-bottom: 20px;
    min-height: 20px;
    word-break: break-all;
  }
  .progress-bar {
    width: 100%;
    height: 6px;
    background: #1e293b;
    border-radius: 9999px;
    overflow: hidden;
    position: relative;
    box-shadow: inset 0 1px 2px rgba(0,0,0,0.4);
  }
  .progress-inner {
    position: absolute;
    height: 100%;
    background: linear-gradient(90deg, #4f46e5, #818cf8);
    border-radius: 9999px;
    width: 35%;
    animation: load 1.2s infinite ease-in-out;
  }
  @keyframes load {
    0% { left: -35%; }
    50% { left: 45%; width: 45%; }
    100% { left: 100%; width: 25%; }
  }
</style>
</head>
<body>
<div class="box">
  <div class="logo-icon">🪣</div>
  <div class="title">Buckezz Desktop</div>
  <div id="status">Wird gestartet und vorbereitet...</div>
  <div class="progress-bar"><div class="progress-inner"></div></div>
</div>
<script>
  function updateStatus(text, isError) {
    var el = document.getElementById('status');
    if (el) {
      el.innerText = text;
      if (isError) el.style.color = '#f87171';
    }
  }
</script>
</body>
</html>"""

def find_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('127.0.0.1', 0))
    port = s.getsockname()[1]
    s.close()
    return port

def wait_for_server(port, timeout=20.0, set_status=None):
    url = f"http://127.0.0.1:{port}/"
    start = time.time()
    attempts = 0
    while time.time() - start < timeout:
        attempts += 1
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'BuckezzDesktop/1.0'})
            with urllib.request.urlopen(req, timeout=1.0) as resp:
                _log(f"wait_for_server: OK code {resp.status} after {attempts} attempts ({time.time() - start:.2f}s)")
                return True
        except urllib.error.HTTPError as e:
            _log(f"wait_for_server: Django responded with HTTP {e.code} after {attempts} attempts")
            return True
        except Exception as e:
            if attempts % 5 == 0:
                _log(f"wait_for_server attempt {attempts}: {e}")
                if set_status:
                    set_status(f"Warte auf lokalen Server (Versuch {attempts})...")
            time.sleep(0.08)
    _log(f"wait_for_server: TIMEOUT after {attempts} attempts ({timeout}s)")
    return False

def init_django_database(set_status=None):
    """Initializes migrations and seed templates quietly."""
    _log("init_django_database: running migrate")
    if set_status: set_status("Führe Datenbank-Migrationen aus...")
    try:
        call_command('migrate', interactive=False)
        _log("migrate: OK")
    except Exception:
        _log(f"migrate ERROR:\n{traceback.format_exc()}")

    _log("init_django_database: running seed_templates")
    if set_status: set_status("Initialisiere Vorlagen...")
    try:
        call_command('seed_templates')
        _log("seed_templates: OK")
    except Exception:
        _log(f"seed_templates ERROR:\n{traceback.format_exc()}")

if __name__ == '__main__':
    _log(f"=== Buckezz Desktop Start === frozen={getattr(sys, 'frozen', False)} pid={os.getpid()}")

    # CLI Support
    if len(sys.argv) > 1:
        arg = sys.argv[1].strip()
        if arg in ('--seed', '--seed-templates'):
            call_command('seed_templates')
            sys.exit(0)
        elif arg == '--manage' and len(sys.argv) > 2:
            cmd_name = sys.argv[2]
            cmd_args = sys.argv[3:]
            call_command(cmd_name, *cmd_args)
            sys.exit(0)

    ui_mode = os.getenv('DESKTOP_UI_MODE', 'window').strip().lower()
    port = find_free_port()
    url = f"http://127.0.0.1:{port}"
    _log(f"Starting ThreadedWSGIServer on port {port}")

    httpd = ThreadedWSGIServer(('127.0.0.1', port), SilentHandler)
    httpd.set_app(application)
    server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    server_thread.start()
    _log("ThreadedWSGIServer thread started")

    for host in ('127.0.0.1', 'localhost'):
        origin = f"http://{host}:{port}"
        if origin not in settings.CSRF_TRUSTED_ORIGINS:
            settings.CSRF_TRUSTED_ORIGINS.append(origin)

    if ui_mode == 'browser':
        init_django_database()
        wait_for_server(port)
        webbrowser.open(url)
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            httpd.shutdown()
            sys.exit(0)
    else:
        import webview

        window = webview.create_window(
            "Buckezz Desktop",
            html=SPLASH_HTML,
            width=1350,
            height=850,
            min_size=(900, 600),
            text_select=True
        )

        def set_ui_status(text, is_error=False):
            try:
                js_text = text.replace("'", "\\'")
                window.evaluate_js(f"updateStatus('{js_text}', {'true' if is_error else 'false'});")
            except Exception:
                pass

        def bootstrap_and_navigate():
            try:
                _log("bootstrap: running DB init")
                init_django_database(set_ui_status)

                _log("bootstrap: waiting for WSGI server")
                if wait_for_server(port, timeout=20.0, set_status=set_ui_status):
                    _log(f"bootstrap: loading {url} into window")
                    set_ui_status("Lade Anwendung...")
                    window.load_url(url)
                    _log("bootstrap: window.load_url called")
                else:
                    _log("bootstrap: Server did not respond within timeout")
                    set_ui_status("Fehler: Server reagiert nicht. Details in buckezz.log", is_error=True)
            except Exception:
                err_msg = traceback.format_exc()
                _log(f"bootstrap CRASH:\n{err_msg}")
                set_ui_status("Fehler beim Start. Details in buckezz.log", is_error=True)

        storage_dir = USER_DATA_DIR / 'webview_data'
        try:
            storage_dir.mkdir(parents=True, exist_ok=True)
            webview.start(bootstrap_and_navigate, private_mode=False, storage_path=str(storage_dir))
        except Exception:
            _log(f"webview.start fallback:\n{traceback.format_exc()}")
            webview.start(bootstrap_and_navigate)

        httpd.shutdown()
        sys.exit(0)
