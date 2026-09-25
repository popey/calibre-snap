#!/bin/sh
# Independent official binary installation used for migration tests.
set -eu
project=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
export CALIBRE_CONFIG_DIRECTORY="$project/migration-test/upstream-config"
export XDG_CACHE_HOME="$project/migration-test/upstream-cache"
export LD_LIBRARY_PATH="$project/migration-test/runtime/usr/lib/x86_64-linux-gnu"
unset LD_PRELOAD QTWEBENGINE_DISABLE_SANDBOX QTWEBENGINE_CHROMIUM_FLAGS
export QT_QPA_PLATFORM="${QT_QPA_PLATFORM:-xcb}"
command=${1:-calibre}
if [ "$#" -gt 0 ]; then shift; fi
case "$command" in
  calibre) exec "$project/migration-test/upstream-9.15.0/calibre" --with-library "$project/migration-test/upstream-library" "$@" ;;
  calibredb|ebook-convert|ebook-viewer|calibre-debug) exec "$project/migration-test/upstream-9.15.0/$command" "$@" ;;
  *) echo 'Expected calibre, calibredb, ebook-convert, ebook-viewer, or calibre-debug' >&2; exit 2 ;;
esac
