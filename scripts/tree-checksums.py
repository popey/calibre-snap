#!/usr/bin/env python3
"""Record/verify file content and symlink targets without opening a Calibre DB."""
import argparse
import hashlib
import json
from pathlib import Path


def inventory(root):
    result = {}
    for path in sorted(root.rglob('*')):
        name = path.relative_to(root).as_posix()
        if path.is_symlink():
            result[name] = {'symlink': str(path.readlink())}
        elif path.is_file():
            with path.open('rb') as stream:
                result[name] = {'bytes': path.stat().st_size,
                                'sha256': hashlib.file_digest(stream, 'sha256').hexdigest()}
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['record', 'verify'])
    parser.add_argument('root', type=Path)
    parser.add_argument('manifest', type=Path)
    args = parser.parse_args()
    if not args.root.is_dir():
        parser.error('Root must be an existing directory')
    actual = inventory(args.root)
    if args.mode == 'record':
        with args.manifest.open('x') as stream:
            json.dump(actual, stream, indent=2, ensure_ascii=False)
            stream.write('\n')
        print(f'Recorded {len(actual)} files: {args.manifest}')
    else:
        expected = json.loads(args.manifest.read_text())
        changed = [name for name in sorted(actual.keys() | expected.keys())
                   if actual.get(name) != expected.get(name)]
        if changed:
            print('Changed/added/removed: ' + '\n'.join(changed))
            raise SystemExit(1)
        print(f'PASS: all {len(actual)} files unchanged in {args.root}')
