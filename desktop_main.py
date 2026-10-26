import os
import sys
import traceback

# Ensure default environment variables BEFORE any Django/WSGI import
if not os.environ.get('SECRET_KEY'):
    os.environ['SECRET_KEY'] = 'django-insecure-desktop-mode-buckezz-key-local-run'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'buckezz_project.settings')

import time
import socket
import threading
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
    width: 380px;
    max-width: 85%;
  }
  .logo-icon {
    font-size: 46px;
    margin-bottom: 12px;
  }
  .title {
    font-size: 26px;
    font-weight: 700;
    margin-bottom: 6px;
    letter-spacing: -0.02em;
    color: #818cf8;
  }
  .sub {
    font-size: 13px;
    color: #94a3b8;
    margin-bottom: 28px;
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
  <div class="sub">Wird gestartet und vorbereitet...</div>
  <div class="progress-bar"><div class="progress-inner"></div></div>
</div>
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
        _log(f"start_server: starting waitress on port {port}")
        serve(application, host='127.0.0.1', port=port, threads=6, _quiet=False)
        _log("start_server: waitress exited")
    except Exception:
        _log(f"start_server ERROR:\n{traceback.format_exc()}")

def wait_for_server(port, timeout=15.0):
    url = f"http://127.0.0.1:{port}"
    start = time.time()
    while time.time() - start < timeout:
        try:
            with urllib.request.urlopen(url, timeout=0.5):
                return True
        except Exception:
            time.sleep(0.05)
    return False

def init_django_database():
    """Initializes migrations and seed templates quietly."""
    from django.db import connections
    _log("init_django_database: running migrate")
    try:
        call_command('migrate', interactive=False)
        _log("migrate: OK")
    except Exception as e:
        _log(f"migrate ERROR: {traceback.format_exc()}")

    _log("init_django_database: running seed_templates")
    try:
        call_command('seed_templates')
        _log("seed_templates: OK")
    except Exception as e:
        _log(f"seed_templates ERROR: {traceback.format_exc()}")

    # Release any held database locks before waitress worker threads connect
    try:
        for conn in connections.all():
            conn.close()
        _log("init_django_database: DB connections closed")
    except Exception:
        pass

if __name__ == '__main__':
    import multiprocessing
    multiprocessing.freeze_support()

    # Ensure default SECRET_KEY if not in environment
    if not os.environ.get('SECRET_KEY'):
        os.environ['SECRET_KEY'] = 'django-insecure-desktop-mode-buckezz-key-local-run'

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'buckezz_project.settings')

    _log(f"=== Buckezz Desktop starting === frozen={getattr(sys, 'frozen', False)}")

    # CLI Support: Allow executing Django management commands via desktop exe
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

    ui_mode = os.getenv('DESKTOP_UI_MODE', 'window').strip().lower()
    port = find_free_port()
    url = f"http://127.0.0.1:{port}"

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

        def bootstrap_and_navigate():
            try:
                _log("bootstrap_and_navigate: start")
                init_django_database()
                _log(f"bootstrap_and_navigate: starting server on port {port}")
                server_thread = threading.Thread(target=start_server, args=(port,), daemon=True)
                server_thread.start()
                _log("bootstrap_and_navigate: waiting for server")
                if wait_for_server(port):
                    _log(f"bootstrap_and_navigate: server ready, loading {url}")
                    window.load_url(url)
                    _log("bootstrap_and_navigate: load_url called")
                else:
                    _log("bootstrap_and_navigate: server NEVER responded (timeout)")
            except Exception:
                _log(f"bootstrap_and_navigate CRASH:\n{traceback.format_exc()}")

        storage_dir = Path(os.getenv('LOCALAPPDATA', str(Path.home()))) / 'Buckezz Desktop' / 'webview_data'
        try:
            storage_dir.mkdir(parents=True, exist_ok=True)
            webview.start(bootstrap_and_navigate, private_mode=False, storage_path=str(storage_dir))
        except Exception:
            webview.start(bootstrap_and_navigate)
        sys.exit(0)
