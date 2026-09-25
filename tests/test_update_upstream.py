import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('updater', 'scripts/update-upstream.py')
updater = importlib.util.module_from_spec(spec)
spec.loader.exec_module(updater)


class ReleasePinTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.manifest = Path(self.directory.name) / 'snapcraft.yaml'
        self.original = Path('snap/snapcraft.yaml').read_text()
        self.manifest.write_text(self.original)
        self.release = {
            'tag_name': 'v99.1.2', 'draft': False, 'prerelease': False,
            'assets': [{
                'name': 'calibre-99.1.2-x86_64.txz',
                'browser_download_url': 'https://github.com/kovidgoyal/calibre/releases/download/v99.1.2/calibre-99.1.2-x86_64.txz',
                'digest': 'sha256:' + 'a' * 64,
            }],
        }

    def test_updates_all_pins_and_is_idempotent(self):
        self.assertEqual(updater.update(self.release, self.manifest), '99.1.2')
        result = self.manifest.read_text()
        self.assertIn("version: '99.1.2'", result)
        self.assertIn('source-checksum: sha256/' + 'a' * 64, result)
        self.assertIn('/v99.1.2/calibre-99.1.2-x86_64.txz', result)
        updater.update(self.release, self.manifest)
        self.assertEqual(result, self.manifest.read_text())

    def test_downgrade_missing_asset_and_replaced_digest(self):
        self.release['tag_name'] = 'v0.0.1'
        with self.assertRaises(ValueError):
            updater.update(self.release, self.manifest)
        self.assertEqual(self.original, self.manifest.read_text())
        self.release['tag_name'] = 'v99.1.2'
        asset = self.release['assets'].pop()
        with self.assertRaises(ValueError):
            updater.update(self.release, self.manifest)
        self.release['assets'].append(asset)
        updater.update(self.release, self.manifest)
        pinned = self.manifest.read_text()
        asset['digest'] = 'sha256:' + 'b' * 64
        with self.assertRaises(ValueError):
            updater.update(self.release, self.manifest)
        self.assertEqual(pinned, self.manifest.read_text())

    def test_rejects_untrusted_metadata_without_writing(self):
        for field, value in [('digest', None), ('browser_download_url', 'https://example.com/bundle')]:
            with self.subTest(field=field):
                asset = self.release['assets'][0]
                original = asset[field]
                asset[field] = value
                with self.assertRaises(ValueError):
                    updater.update(self.release, self.manifest)
                self.assertEqual(self.original, self.manifest.read_text())
                asset[field] = original
        self.release['prerelease'] = True
        with self.assertRaises(ValueError):
            updater.update(self.release, self.manifest)
        self.assertEqual(self.original, self.manifest.read_text())


if __name__ == '__main__':
    unittest.main()
