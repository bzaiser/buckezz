import os
import sys
import time
import socket
import threading
import traceback
import urllib.request
import webbrowser
from pathlib import Path
from waitress import serve
from buckezz_project.wsgi import application
from django.conf import settings
from django.core.management import call_command

LOG_DIR = Path(os.getenv('LOCALAPPDATA', str(Path.home()))) / 'Buckezz Desktop'
LOG_FILE = LOG_DIR / 'buckezz.log'

def _log(msg):
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(f"[{time.strftime('%H:%M:%S')}] {msg}\n")
    except Exception:
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

def start_server(port):
    try:
        _log(f"waitress: starting on port {port}")
        serve(application, host='127.0.0.1', port=port, threads=6, _quiet=False)
        _log("waitress: stopped")
    except Exception:
        _log(f"waitress CRASH:\n{traceback.format_exc()}")

def wait_for_server(port, timeout=20.0, set_status=None):
    url = f"http://127.0.0.1:{port}"
    start = time.time()
    attempts = 0
    while time.time() - start < timeout:
        attempts += 1
        try:
            with urllib.request.urlopen(url, timeout=0.5):
                _log(f"wait_for_server: OK after {attempts} attempts ({time.time() - start:.2f}s)")
                return True
        except Exception as e:
            if attempts % 10 == 0:
                _log(f"wait_for_server attempt {attempts}: {e}")
                if set_status:
                    set_status(f"Warte auf lokalen Server (Versuch {attempts})...")
            time.sleep(0.08)
    _log(f"wait_for_server: TIMEOUT after {attempts} attempts ({timeout}s)")
    return False

def init_django_database(set_status=None):
    """Initializes migrations and templates quietly."""
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
    # Ensure default environment variables
    if not os.environ.get('SECRET_KEY'):
        os.environ['SECRET_KEY'] = 'django-insecure-desktop-mode-buckezz-key-local-run'
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'buckezz_project.settings')

    _log(f"=== Buckezz Desktop Start === frozen={getattr(sys, 'frozen', False)} pid={os.getpid()}")

    if len(sys.argv) > 1:
        import django
        django.setup()
        arg = sys.argv[1].strip()
        if arg in ('--seed', '--seed-templates'):
            call_command('seed_templates')
            sys.exit(0)
        elif arg == '--manage' and len(sys.argv) > 2:
            cmd_name = sys.argv[2]
            cmd_args = sys.argv[3:]
            call_command(cmd_name, *cmd_args)
            sys.exit(0)

    import django
    django.setup()
    _log("django.setup: OK")

    ui_mode = os.getenv('DESKTOP_UI_MODE', 'window').strip().lower()
    port = find_free_port()
    url = f"http://127.0.0.1:{port}"
    _log(f"Free port assigned: {port}")

    for host in ('127.0.0.1', 'localhost'):
        origin = f"http://{host}:{port}"
        if origin not in settings.CSRF_TRUSTED_ORIGINS:
            settings.CSRF_TRUSTED_ORIGINS.append(origin)

    if ui_mode == 'browser':
        init_django_database()
        server_thread = threading.Thread(target=start_server, args=(port,), daemon=True)
        server_thread.start()
        wait_for_server(port)
        webbrowser.open(url)
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
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

                _log("bootstrap: starting waitress thread")
                set_ui_status("Starte lokalen Server...")
                server_thread = threading.Thread(target=start_server, args=(port,), daemon=True)
                server_thread.start()

                _log("bootstrap: waiting for waitress")
                if wait_for_server(port, timeout=20.0, set_status=set_ui_status):
                    _log(f"bootstrap: loading {url} into window")
                    set_ui_status("Lade Anwendung...")
                    window.load_url(url)
                    _log("bootstrap: window.load_url called")
                else:
                    _log("bootstrap: Server did not respond within timeout")
                    set_ui_status("Fehler: Server reagiert nicht. Siehe buckezz.log", is_error=True)
            except Exception:
                err_msg = traceback.format_exc()
                _log(f"bootstrap CRASH:\n{err_msg}")
                set_ui_status("Fehler beim Start. Details in buckezz.log", is_error=True)

        storage_dir = Path(os.getenv('LOCALAPPDATA', str(Path.home()))) / 'Buckezz Desktop' / 'webview_data'
        try:
            storage_dir.mkdir(parents=True, exist_ok=True)
            webview.start(bootstrap_and_navigate, private_mode=False, storage_path=str(storage_dir))
        except Exception:
            _log(f"webview.start fallback:\n{traceback.format_exc()}")
            webview.start(bootstrap_and_navigate)
        sys.exit(0)
