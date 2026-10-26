# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

datas = [
    ('templates', 'templates'),
    ('static', 'static'),
    ('core', 'core'),
]

import os
if os.path.exists('.env'):
    datas.append(('.env', '.'))
if os.path.exists('clean_template.sqlite3'):
    datas.append(('clean_template.sqlite3', '.'))

datas += collect_data_files('core')
datas += collect_data_files('admin_interface')
datas += collect_data_files('colorfield')

hiddenimports = [
    'waitress',
    'webview',
    'clr',
    'django',
    'django.core',
    'django.core.management',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'django.db.backends.sqlite3',
    'core',
    'core.management',
    'core.management.commands',
    'core.management.commands.seed_templates',
    'core.management.commands.build_template_db',
    'core.management.commands.seed_demo_data',
    'core.management.commands.setup_groups',
    'core.management.commands.send_reminders',
    'core.management.commands.migrate_all',
    'core.management.commands.export_tenant_theme',
    'core.management.commands.seed_tenant_theme',
    'core.management.commands.set_tenant_password',
    'buckezz_project',
    'buckezz_project.wsgi',
    'buckezz_project.settings',
    'buckezz_project.urls',
    'admin_interface',
    'colorfield',
    'whitenoise',
    'whitenoise.middleware',
    'whitenoise.storage',
    'pwa',
    'django_htmx',
    'xhtml2pdf',
]
hiddenimports += collect_submodules('core')
hiddenimports += collect_submodules('admin_interface')
hiddenimports += collect_submodules('colorfield')

a = Analysis(
    ['desktop_main.py'],
    pathex=['.'],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='BuckezzDesktop',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='static/img/app.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='BuckezzDesktop',
)
