#!/usr/bin/env python3
"""Exercise the installed strict snap on an isolated X11 desktop.

Run through xvfb-run; requires openbox, xdotool and scrot.
Uses generated books only, and a private Calibre configuration.
"""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time

reports = Path(os.environ.get('CALIBRE_TEST_REPORTS', 'artifacts/app-tests')).resolve()
reports.mkdir(parents=True, exist_ok=True)
work = Path(tempfile.mkdtemp(prefix='calibre-gui-test-', dir=Path.home()))
(reports / 'test-location.txt').write_text(str(work) + '\n')
env = dict(os.environ, CALIBRE_TEST_ROOT=str(work), QT_QPA_PLATFORM='xcb')
# Use the real installed command chain, then override only writable test locations.
chain = '''exec "$SNAP/snap/command-chain/gpu-2404-wrapper" \
"$SNAP/snap/command-chain/desktop-launch" "$SNAP/bin/calibre-env" \
env CALIBRE_CONFIG_DIRECTORY="$CALIBRE_TEST_ROOT/config" \
XDG_CACHE_HOME="$CALIBRE_TEST_ROOT/cache" "$SNAP/opt/calibre/$0" "$@"'''
children = []
streams = []


def command(app, *args):
    plug = {'calibredb': 'calibre.calibredb', 'ebook-convert': 'calibre.ebook-convert',
            'ebook-viewer': 'calibre.ebook-viewer'}.get(app, 'calibre')
    return ['snap', 'run', '--shell', plug, '-c', chain, app, *map(str, args)]


def run(app, *args):
    result = subprocess.run(command(app, *args), env=env, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120)
    with (reports / 'commands.log').open('a') as log:
        log.write(f'{app} {args}\n{result.stdout}\n{result.stderr}\n')
    result.check_returncode()
    return result.stdout


def start(app, *args):
    log = (reports / f'{app}.log').open('w')
    streams.append(log)
    process = subprocess.Popen(command(app, *args), env=env, stdout=log, stderr=log)
    children.append(process)
    return process


def xdo(*args):
    return subprocess.run(['xdotool', *map(str, args)], text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5)


def window(process, title):
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f'App exited before opening {title}: {process.returncode}')
        result = xdo('search', '--onlyvisible', '--name', title)
        if result.returncode == 0:
            return result.stdout.splitlines()[-1]
        time.sleep(0.5)
    raise RuntimeError(f'No visible window matching {title}')


def capture(wid, name):
    xdo('windowsize', wid, 1200, 740).check_returncode()
    xdo('windowmove', wid, 20, 20).check_returncode()
    xdo('windowactivate', '--sync', wid).check_returncode()
    time.sleep(2)
    subprocess.run(['scrot', str(reports / name)], check=True, timeout=10)


try:
    wm_log = (reports / 'openbox.log').open('w')
    streams.append(wm_log)
    children.append(subprocess.Popen(['openbox'], stdout=wm_log, stderr=wm_log))
    (work / 'input.html').write_text('''<html><head><title>Calibre GUI Test</title></head>
<body><h1>Calibre GUI Test</h1><p>Reading and conversion regression test.</p>
<div style="page-break-before:always"><h1>Second page</h1><p>Navigation works.</p></div>
</body></html>''')
    run('ebook-convert', work / 'input.html', work / 'book.epub')
    library = work / 'library'
    run('calibredb', 'add', '--with-library', library, work / 'book.epub')
    books = json.loads(run('calibredb', 'list', '--with-library', library, '--for-machine'))
    assert len(books) == 1 and books[0]['title'] == 'Calibre GUI Test', books
    book_id = str(books[0]['id'])
    run('calibredb', 'set_metadata', '--with-library', library, book_id,
        '--field', 'title:Calibre GUI Test — edited')
    books = json.loads(run('calibredb', 'list', '--with-library', library, '--for-machine'))
    assert books[0]['title'] == 'Calibre GUI Test — edited', books
    # Skip onboarding only; launch the normal installed manager below.
    run('calibre-debug', '-c',
        'from calibre.gui2 import dynamic; dynamic.set("welcome_wizard_was_run", True)')
    manager = start('calibre', '--no-update-check', '--with-library', library)
    manager_window = window(manager, r'^calibre.*library')
    capture(manager_window, 'manager.png')
    assert manager.poll() is None, 'Manager crashed'
    # A second launch must contact the existing GUI through the socket adapter.
    run('calibre', '--no-update-check', '--with-library', library)
    run('calibre', '--shutdown-running-calibre')
    assert manager.wait(timeout=30) == 0, 'Manager failed during shutdown'
    # Reopen the database after GUI shutdown, never concurrently with it.
    books = json.loads(run('calibredb', 'list', '--with-library', library, '--for-machine'))
    assert next(b for b in books if str(b['id']) == book_id)['title'] == 'Calibre GUI Test — edited', books
    assert all(str(b['id']) == book_id or b['title'] == 'Quick Start Guide' for b in books), books
    viewer = start('ebook-viewer', work / 'book.epub')
    viewer_window = window(viewer, r'Calibre GUI Test.*E-book viewer')
    capture(viewer_window, 'viewer-start.png')
    xdo('key', '--clearmodifiers', 'space').check_returncode()  # dismiss first-run help
    time.sleep(2)
    capture(viewer_window, 'viewer-before-page.png')
    xdo('key', '--clearmodifiers', 'Right').check_returncode()
    time.sleep(2)
    capture(viewer_window, 'viewer-after-page.png')
    assert viewer.poll() is None, 'Viewer crashed'
    assert (reports / 'viewer-before-page.png').read_bytes() != (reports / 'viewer-after-page.png').read_bytes(), 'Viewer did not visually change after navigation'
    xdo('key', '--clearmodifiers', 'alt+F4').check_returncode()
    assert viewer.wait(timeout=30) == 0, 'Viewer failed during shutdown'
    (reports / 'result.txt').write_text('PASS: import, edit, manager launch/reopen, single-instance IPC, viewer launch/navigation\n')
    print((reports / 'result.txt').read_text(), end='')
finally:
    # Preserve diagnostics and generated data even on failure; stop only our children.
    for child in reversed(children):
        if child.poll() is None:
            child.terminate()
            try:
                child.wait(timeout=10)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()
    for stream in streams:
        stream.close()
