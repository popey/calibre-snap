#!/bin/sh
# Run the actual Calibre lookup with a test-only mount-table provider. No device
# is mounted or written to, and no library is opened. An optional absolute path
# selects a locally compiled prototype instead of the installed adapter.
set -eu
mkdir -p artifacts/app-tests
work=$(mktemp -d "$PWD/artifacts/app-tests/mount-compat.XXXXXX")
cc -shared -fPIC -O2 -Wall -Wextra -Werror tests/mount-fixture.c -ldl \
  -o "$work/fixture.so"
: > "$work/mounts"
export CALIBRE_MOUNT_TEST_ROOT="$work"
export CALIBRE_MOUNT_TEST_SCRIPT="$PWD/scripts/mount-compat-probe.py"
export CALIBRE_MOUNT_TEST_COMPAT="${1:-}"
snap run --shell calibre -c '
  exec "$SNAP/bin/calibre-env" env \
    CALIBRE_SNAP_FILTER_MOUNTS=1 \
    LD_PRELOAD="${CALIBRE_MOUNT_TEST_COMPAT:-$SNAP/lib/libcalibre-snap-compat.so}:$CALIBRE_MOUNT_TEST_ROOT/fixture.so" \
    TEST_MOUNTS_FILE="$CALIBRE_MOUNT_TEST_ROOT/mounts" \
    "$SNAP/opt/calibre/calibre-debug" -e "$CALIBRE_MOUNT_TEST_SCRIPT"
'
