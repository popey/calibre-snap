"""Exercise the compiled preload through real libc and Python file opens."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


HOSTFS = '/var/lib/snapd/hostfs'


def row(target, source='/dev/mockkindle', options='rw,nosuid,nodev', kind='vfat'):
    return f'{source} {target} {kind} {options} 0 0\n'


class MountCompatibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.directory.cleanup)
        cls.root = Path(cls.directory.name)
        cls.compat = cls.root / 'compat.so'
        cls.fixture = cls.root / 'fixture.so'
        for output, sources in [
            (cls.compat, ['snap/socket-compat/socket-compat.c', 'snap/socket-compat/mount-compat.c']),
            (cls.fixture, ['tests/mount-fixture.c']),
        ]:
            subprocess.run(['cc', '-shared', '-fPIC', '-O2', '-Wall', '-Wextra', '-Werror',
                            *sources, '-ldl', '-o', str(output)], check=True)

    def setUp(self):
        self.mounts = self.root / 'mounts'
        self.env = dict(os.environ, CALIBRE_SNAP_FILTER_MOUNTS='1',
                        LD_PRELOAD=f'{self.compat}:{self.fixture}', TEST_MOUNTS_FILE=str(self.mounts))
        self.env.pop('TEST_MOUNTS_DENIED', None)
        self.env.pop('TEST_MEMFD_DENIED', None)

    def run_python(self, code, *args):
        return subprocess.run([sys.executable, '-c', code, *map(str, args)],
                              env=self.env, capture_output=True, text=True, check=True).stdout

    def filtered(self, contents, path='/proc/mounts'):
        self.mounts.write_text(contents)
        return self.run_python('import sys; print(open(sys.argv[1]).read(), end="")', path)

    def test_duplicate_orders_and_supported_paths(self):
        for target in ['/media/test/Kindle', '/run/media/test/My\\040Kindle', '/mnt/Kindle']:
            normal, host = row(target), row(HOSTFS + target)
            for contents in (host + normal, normal + host):
                with self.subTest(target=target, contents=contents):
                    self.assertEqual(self.filtered(contents), normal)
                    self.assertEqual(self.filtered(contents, '/proc/self/mounts'), normal)

    def test_preserves_unmatched_and_unrelated_entries_byte_for_byte(self):
        contents = ('malformed\n\n' + row(HOSTFS + '/run/media/test/Kindle') +
                    row('/run/media/test/Kindle', source='/dev/other') +
                    row(HOSTFS + '/home/test') + row('/home/test') +
                    row(HOSTFS + '/media/test/net', source='server:/share', kind='nfs') +
                    row('/media/test/net', source='server:/share', kind='nfs') +
                    row('/mnt/only-normal') + 'no trailing newline')
        self.assertEqual(self.filtered(contents), contents)

    def test_requires_exact_path_type_and_options(self):
        host = row(HOSTFS + '/media/test/Kindle')
        for other in [row('/media/test/Different'), row('/media/test/Kindle', kind='ext4'),
                      row('/media/test/Kindle', options='ro,nosuid,nodev'),
                      row('/media/test/Kindle', source='/dev/other')]:
            with self.subTest(other=other):
                self.assertEqual(self.filtered(host + other), host + other)

    def test_disabled_and_snapshot_failure_leave_table_unchanged(self):
        contents = row(HOSTFS + '/mnt/Kindle') + row('/mnt/Kindle')
        self.env['CALIBRE_SNAP_FILTER_MOUNTS'] = '0'
        self.assertEqual(self.filtered(contents), contents)
        self.env['CALIBRE_SNAP_FILTER_MOUNTS'] = '1'
        self.env['TEST_MEMFD_DENIED'] = '1'
        self.assertEqual(self.filtered(contents), contents)

    def test_permission_error_is_preserved(self):
        self.env['TEST_MOUNTS_DENIED'] = '1'
        self.run_python('''
import errno
try:
    open('/proc/mounts')
except PermissionError as error:
    assert error.errno == errno.EACCES
else:
    raise AssertionError('mount-observe denial was hidden')
''')

    def test_fresh_snapshot_readonly_seek_cloexec_and_unrelated_io(self):
        self.mounts.write_text(row(HOSTFS + '/mnt/Kindle') + row('/mnt/Kindle'))
        self.run_python('''
import errno, fcntl, os, sys
from pathlib import Path
first = open('/proc/mounts', 'rb')
assert b'hostfs' not in first.read()
first.seek(0)
expected = first.read()
assert fcntl.fcntl(first.fileno(), fcntl.F_GETFL) & os.O_ACCMODE == os.O_RDONLY
assert fcntl.fcntl(first.fileno(), fcntl.F_GETFD) & fcntl.FD_CLOEXEC
try:
    os.write(first.fileno(), b'bad')
except OSError as error:
    assert error.errno == errno.EBADF
else:
    raise AssertionError('snapshot was writable')
Path(sys.argv[1]).write_text('/dev/other /mnt/new vfat rw 0 0\\n')
assert open('/proc/mounts').read() == '/dev/other /mnt/new vfat rw 0 0\\n'
first.seek(0)
assert first.read() == expected
first.close()
ordinary = Path(sys.argv[2])
fd = os.open(ordinary, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
os.write(fd, b'unchanged')
os.close(fd)
assert ordinary.read_bytes() == b'unchanged'
assert ordinary.stat().st_mode & 0o777 == 0o600
ordinary.unlink()
''', self.mounts, self.root / 'ordinary-file')

    def test_all_interposed_entry_points(self):
        self.mounts.write_text(row(HOSTFS + '/mnt/Kindle') + row('/mnt/Kindle'))
        self.run_python('''
import ctypes, os
libc = ctypes.CDLL(None, use_errno=True)
for name in ('open', 'open64', 'openat', 'openat64'):
    fn = getattr(libc, name)
    fn.restype = ctypes.c_int
    for flags in (os.O_RDONLY, os.O_RDONLY | os.O_CLOEXEC):
        args = [b'/proc/mounts', flags]
        if name.startswith('openat'):
            args.insert(0, -100)
        fd = fn(*args)
        assert fd >= 0, (name, ctypes.get_errno())
        assert b'hostfs' not in os.read(fd, 4096), name
        assert os.get_inheritable(fd) == (not flags & os.O_CLOEXEC)
        os.close(fd)
libc.fread.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_size_t, ctypes.c_void_p]
libc.fread.restype = ctypes.c_size_t
libc.fclose.argtypes = [ctypes.c_void_p]
for name in ('fopen', 'fopen64'):
    fn = getattr(libc, name)
    fn.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
    fn.restype = ctypes.c_void_p
    stream = fn(b'/proc/mounts', b'rbe')
    assert stream, (name, ctypes.get_errno())
    buf = ctypes.create_string_buffer(4096)
    n = libc.fread(buf, 1, 4096, stream)
    assert n and b'hostfs' not in buf.raw[:n], name
    libc.fclose(stream)
''')

    def test_no_descriptor_leak_and_update_opens_are_untouched(self):
        contents = row(HOSTFS + '/mnt/Kindle') + row('/mnt/Kindle')
        self.mounts.write_text(contents)
        self.run_python('''
import os
before = len(os.listdir('/proc/self/fd'))
for i in range(100):
    with open('/proc/mounts') as stream:
        assert 'hostfs' not in stream.read()
assert len(os.listdir('/proc/self/fd')) == before
with open('/proc/mounts', 'r+') as stream:
    assert 'hostfs' in stream.read()
''')

    def test_large_table_falls_back_without_truncation(self):
        # The memory bound must preserve the entire original file on fallback.
        contents = row(HOSTFS + '/mnt/Kindle') + row('/mnt/Kindle') + 'x' * (16 * 1024 * 1024)
        self.assertEqual(self.filtered(contents), contents)


if __name__ == '__main__':
    unittest.main()
