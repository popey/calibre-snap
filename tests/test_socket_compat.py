"""Exercise the actual compiled adapter across bind/connect, not a Python model."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class SocketCompatibilityTests(unittest.TestCase):
    def test_calibre_sockets_are_namespaced_and_other_sockets_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            library = str(Path(directory) / 'compat.so')
            subprocess.run(['cc', '-shared', '-fPIC', '-Wall', '-Wextra', '-Werror',
                            'snap/socket-compat/socket-compat.c', '-ldl', '-o', library], check=True)
            env = dict(os.environ, LD_PRELOAD=library)
            subprocess.run([sys.executable, '-c', r'''
import os
import socket
suffix = str(os.getpid())
for name, expected in [
    ('calibre-singleinstance-' + suffix, 'snap.calibre.calibre-singleinstance-' + suffix),
    ('test-calibre-gui-' + suffix, 'snap.calibre.test-calibre-gui-' + suffix),
    ('unrelated-' + suffix, 'unrelated-' + suffix),
]:
    with socket.socket(socket.AF_UNIX) as server, socket.socket(socket.AF_UNIX) as client:
        server.bind('\0' + name)
        assert server.getsockname() == ('\0' + expected).encode()
        server.listen(1)
        client.connect('\0' + name)
        connection, _ = server.accept()
        with connection:
            client.sendall(b'calibre')
            assert connection.recv(7) == b'calibre'
'''], env=env, check=True)
