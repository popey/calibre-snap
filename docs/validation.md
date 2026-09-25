# Local validation — 2026-09-24

Historical proof for the former `calibre-unofficial` name. See
[the confinement audit](flatpak-issue-audit.md) for validation after renaming to `calibre`.

Calibre 9.15.0, amd64, core24, strict confinement. Built with Snapcraft 9.1.2
using `snapcraft --use-lxd`, installed as local revision x3.

Artifact: `calibre-unofficial_9.15.0_amd64.snap` (about 284 MiB).
SHA-256: `2a24f2eaf0ae37c30b7b40c4eb83ff4c031f148db676397cbb5d66e7a604b783`.

Passed:

- LXD build and installation of the resulting snap.
- `scripts/smoke-test.sh`: HTML-to-EPUB conversion, import into a new library,
  and database listing of the imported book.
- First-run wizard and main library window on the local X11 desktop.
- Opening the imported EPUB from the GUI and through the standalone
  `calibre-unofficial.ebook-viewer` command; visible rendered cover.
- Three regression tests covering release updates, rejection of invalid release
  metadata, and socket namespace translation including bind/connect.
- GitHub Actions workflow checked with actionlint 1.7.7.

Local evidence (ignored by git): `artifacts/build.log`, `artifacts/library.png`,
`artifacts/viewer.png`. The tested sample library is
`/home/minnie/calibre-snap-smoke.ZwXCpS/library`.

The `raw-usb` plug was connected locally to permit USB enumeration. Before
connecting it, Calibre's device scanner logged a permission error. No physical
reader transfer, MTP, printing, third-party plugin or content-server test was
performed. Removable-media and cups remain unconnected.

The desktop logs retain nonfatal session-management, graphics fallback and
Chromium OOM-score permission messages. Snapcraft retains warnings for unused
libraries and optional upstream Qt plugins with absent dependencies. These
features have not been certified by the successful basic tests.

Run the database smoke test before starting the GUI: Calibre's global
single-instance lock prevents simultaneous database CLI and main GUI access,
even when the test uses a separate library.

The GitHub workflow has been created and linted locally, but no remote repository
was configured in this workspace, so it has not been pushed or run on GitHub.
It rebuilds the latest stable upstream release daily and retains artifacts;
it does not publish to the Snap Store.
