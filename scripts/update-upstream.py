#!/usr/bin/env python3
"""Pin a newer stable official Linux bundle and its GitHub SHA-256 digest."""
import argparse
import json
import os
from pathlib import Path
import re
import urllib.request


def current_version(manifest):
    match = re.search(r"^version: ['\"]?(\d+\.\d+\.\d+)['\"]?\s*$", manifest.read_text(), re.MULTILINE)
    if not match:
        raise ValueError('Expected one numeric manifest version')
    return match[1]


def update(release, manifest):
    tag = release['tag_name']
    if release.get('prerelease') or release.get('draft') or not re.fullmatch(r'v\d+\.\d+\.\d+', tag):
        raise ValueError('Expected a stable numeric Calibre release')
    version = tag[1:]
    current = current_version(manifest)
    if tuple(map(int, version.split('.'))) < tuple(map(int, current.split('.'))):
        raise ValueError(f'Refusing downgrade from {current} to {version}')
    name = f'calibre-{version}-x86_64.txz'
    assets = [a for a in release['assets'] if a['name'] == name]
    if len(assets) != 1:
        raise ValueError('Expected exactly one amd64 Linux bundle')
    asset = assets[0]
    digest = asset.get('digest') or ''
    if not re.fullmatch(r'sha256:[0-9a-f]{64}', digest):
        raise ValueError('Release asset has no SHA-256 digest')
    url = f'https://github.com/kovidgoyal/calibre/releases/download/{tag}/{name}'
    if asset['browser_download_url'] != url:
        raise ValueError('Unexpected release download URL')
    text = manifest.read_text()
    # A re-upload of an already pinned version must not silently change its hash.
    if version == current:
        if f'    source: {url}\n' not in text or f'    source-checksum: {digest.replace(":", "/", 1)}\n' not in text:
            raise ValueError('Existing release asset changed; manual review required')
        return version
    for pattern, replacement in [
        (r"^version: .*", f"version: '{version}'"),
        (r'^    source: https://github.com/kovidgoyal/calibre/releases/download/.*', f'    source: {url}'),
        (r'^    source-checksum: .*', f'    source-checksum: {digest.replace(":", "/", 1)}'),
    ]:
        text, count = re.subn(pattern, replacement, text, flags=re.MULTILINE)
        if count != 1:
            raise ValueError(f'Expected exactly one match for {pattern}')
    manifest.write_text(text)
    return version


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--github-output', type=Path)
    args = parser.parse_args()
    headers = {'Accept': 'application/vnd.github+json', 'User-Agent': 'calibre-snap'}
    if os.environ.get('GH_TOKEN'):
        headers['Authorization'] = 'Bearer ' + os.environ['GH_TOKEN']
    request = urllib.request.Request('https://api.github.com/repos/kovidgoyal/calibre/releases/latest', headers=headers)
    with urllib.request.urlopen(request, timeout=60) as response:
        release = json.load(response)
    manifest = Path('snap/snapcraft.yaml')
    current = current_version(manifest)
    latest = update(release, manifest)
    if args.github_output:
        with args.github_output.open('a') as stream:
            stream.write(f'current={current}\nlatest={latest}\nneeds_update={str(current != latest).lower()}\n')
    print(f'{current} -> {latest}' if current != latest else f'Already current: {latest}')
