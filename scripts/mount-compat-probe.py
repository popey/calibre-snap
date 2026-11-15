"""Invoked by mount-compat-smoke-test.sh in the confined Calibre runtime."""
import os
from pathlib import Path

from calibre.devices.udisks import node_mountpoint


def main():
    fixture = Path(os.environ['TEST_MOUNTS_FILE'])
    target = '/run/media/test/My\\040Kindle'
    hostfs = '/var/lib/snapd/hostfs' + target
    normal = f'/dev/mockkindle {target} vfat rw,nosuid,nodev 0 0\n'
    host = f'/dev/mockkindle {hostfs} vfat rw,nosuid,nodev 0 0\n'
    fixture.write_text(host + normal)

    os.environ['CALIBRE_SNAP_FILTER_MOUNTS'] = '0'
    assert node_mountpoint('/dev/mockkindle') == hostfs.replace('\\040', ' ')
    print('Control: unfiltered Calibre selects the hostfs entry')

    os.environ['CALIBRE_SNAP_FILTER_MOUNTS'] = '1'
    for table in (host + normal, normal + host):
        fixture.write_text(table)
        assert node_mountpoint('/dev/mockkindle') == target.replace('\\040', ' ')
        print('Filtered Calibre selects /run/media/test/My Kindle')

    # A new open must reflect hotplug changes, not a startup-time cache.
    fixture.write_text('')
    assert node_mountpoint('/dev/mockkindle') is None
    fixture.write_text(normal.replace('My\\040Kindle', 'Reconnected'))
    assert node_mountpoint('/dev/mockkindle') == '/run/media/test/Reconnected'
    print('Calibre sees removal and reconnection on subsequent lookups')

    # Missing permission must still surface; this is not an access workaround.
    os.environ['TEST_MOUNTS_DENIED'] = '1'
    try:
        node_mountpoint('/dev/mockkindle')
    except PermissionError:
        print('Mount-table permission denial remains visible')
    else:
        raise AssertionError('Expected PermissionError')
    finally:
        del os.environ['TEST_MOUNTS_DENIED']

    # Disable the test provider and exercise the real, currently mounted table.
    del os.environ['TEST_MOUNTS_FILE']
    assert node_mountpoint('/dev/calibre-snap-smoke-test-nonexistent') is None
    print('Real mount-table lookup passed')
    print('Confined mount compatibility probe passed (synthetic reader, no transfer)')


if __name__ == '__main__':
    main()
