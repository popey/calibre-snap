# Calibre snap

Maintainer context and current recorded state: [project handover](docs/handover.md).

Community packaging of [Calibre](https://calibre-ebook.com/).
Not affiliated with or supported by the upstream project. Please report snap
packaging issues here, not to Calibre's developer.

The snap uses **core24**, **strict confinement**, and the official **amd64 Linux
binary bundle**, pinned by version and SHA-256. It builds a snap from upstream
binaries; it does not compile Calibre from source. The GNOME extension supplies
desktop integration and graphics support; Calibre supplies its own Qt/Python.

## Install

```sh
snap install calibre
```

Published as [calibre on the Snap Store](https://snapcraft.io/calibre).

## Build and install locally

With Snapcraft and an initialized LXD installation:

```sh
snapcraft --use-lxd
snap install --dangerous ./calibre_*.snap
calibre
```

Other commands:

```sh
calibre.ebook-viewer book.epub
calibre.ebook-convert book.epub book.pdf
calibre.calibredb --help
```

Use a library in a non-hidden directory under your home. Configuration lives in
`~/snap/calibre/current/config`; caches live under `common/.cache`.
The launcher defaults to X11/XWayland and Fusion styling. Qt WebEngine's internal
sandbox is disabled for compatibility with snap confinement; the snap itself
remains strictly confined. WebEngine uses the snap's temporary directory for
shared-memory files (`--disable-dev-shm-usage`).

Device access (not connected automatically):

```sh
snap connect calibre:removable-media
snap connect calibre:raw-usb
```

Connect `raw-usb` to enable the device scanner; without it Calibre logs a
permission error while scanning `/sys/bus/usb/devices`. Mounted readers may work
via removable-media. USB/MTP device access, printing,
plugins, and the content server need separate testing. This proof of concept
does not establish full device compatibility. Hidden host directories and
arbitrary filesystem paths are outside the normal `home` interface access.

## Upstream updates and GitHub Actions

The repository target is `popey/calibre-snap`. `build.yml` builds the checked-in pin on
pushes to `main`, pull requests and manual requests. The separate
`sync-version-with-upstream.yml` checks daily at 06:23 UTC and on manual requests.
It validates a newer stable upstream release, updates version/URL/SHA-256 together,
builds with LXD, installs the snap and tests HTML→EPUB, EPUB→old/both MOBI,
EPUB→PDF, and library import, then runs manager/viewer tests on an isolated X11
desktop before opening/updating `auto-update-calibre`. The desktop test verifies
metadata edits survive reopening, single-instance communication, clean shutdown,
and viewer navigation. Logs and screenshots are retained as app-test artifacts,
including on failure. This is automated regression coverage, not a guarantee for
every device, plugin, or desktop environment.
Unchanged versions do nothing. Downgrades, prereleases, missing digests and changed
assets for an already-pinned version fail rather than silently changing the pin.

This follows the build-before-PR approach in `popey/bombsquad-snap`, and the daily
PR pattern in `popey/dosbox-staging-snap` and `popey/fab-agon-emulator-snap`.
Only `snap/snapcraft.yaml` is committed by the bot. The snap and resolved manifest
are retained as workflow artifacts for 14 days. Nothing auto-merges or publishes
to the Snap Store.

Enable Actions on the default branch and enable **Allow GitHub Actions to create
and approve pull requests** in Settings → Actions → General. Repository policy
must permit the workflow's contents/pull-requests write permissions. No extra
secret or PAT is needed: it uses `GITHUB_TOKEN`. GitHub-generated PR checks may
require approval; the update workflow already builds/tests before creating the PR
and links that validation run. See [GitHub's trigger rules](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow).

For a local version update: `python3 scripts/update-upstream.py`. The checker
tracks stable releases in `kovidgoyal/calibre`, rather than every upstream commit.

## Name transition

The snap is now named `calibre`; its main command is `calibre`, with
`calibre.ebook-viewer`, `calibre.ebook-convert`, and `calibre.calibredb` subcommands.
It remains unofficial and unsupported by the upstream project. The old
`calibre-unofficial` proof-of-concept is a different snap, with separate settings;
installing `calibre` does not migrate its configuration or remove it. Keep your
library outside snap data and follow the [migration procedure](docs/migration.md).
Earlier validation records retain the old name intentionally.

## Snap compatibility layer

The launcher limits `LD_LIBRARY_PATH` to three runtime directories because the
upstream native launcher rejects the extension's longer default path. Upstream
adds its own bundled library directory.

A small C adapter (`snap/socket-compat/socket-compat.c`) prefixes Calibre's
abstract Unix sockets with `snap.calibre.` to meet snapd's socket
namespace rules. It covers bind and connect, including Qt and child processes;
it leaves other sockets alone. The upstream binary bundle is unmodified.
Regression tests compile and exercise the adapter as well as the release updater.

Snapcraft reports unused bundled libraries and missing dependencies for optional
upstream Qt plugins (such as EGLFS and QtPdf). These warnings remain visible;
they do not by themselves establish that those optional features work.

See [local validation results](docs/validation.md) for tested behavior and limitations.

See [migration procedure and test results](docs/migration.md) before adopting an existing library.

See the [Flatpak issue audit](docs/flatpak-issue-audit.md) for all 79 issues reviewed, mitigations, and remaining compatibility tests.

Latest rebuild and regression results: [2026-09-25 retest](docs/retest-2026-09-25.md).

To run the desktop regression test locally (with no other Calibre instances
running), install Xvfb, xauth, Openbox, xdotool and scrot, then run:

```sh
xvfb-run -a -s '-screen 0 1280x800x24' python3 scripts/gui-smoke-test.py
```

The script uses generated books and private test preferences under your home,
leaves evidence in `artifacts/app-tests/`, and does not use your existing library.
