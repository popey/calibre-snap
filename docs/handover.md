# Project handover — 2026-09-27

This records the state established during development, rather than a live Store
or GitHub status check. Recheck remote state before a future release.

## Update — 2026-10-11: automated desktop coverage

The common build action now runs an isolated Xvfb/Openbox desktop test as well as
conversion/database smoke tests, for both ordinary builds and upstream-update
PRs. `scripts/gui-smoke-test.py` uses generated books and separate configuration,
checks import/edit/reopen, actual manager startup and single-instance IPC, then
viewer launch/navigation. It saves screenshots and logs even on failure. It does
not claim hardware, plugin, Wayland or comprehensive rendering coverage.

## Update — 2026-10-11: 9.16.0 candidate

- Fast-forwarded local main to `6e4915d`, the merged upstream-update PR #1.
  Only the recipe version, archive URL and checksum changed remotely. Existing
  uncommitted documentation and Store-copy work was preserved.
- Verified GitHub upstream release v9.16.0 (published October 9) and its amd64
  archive digest: `03cd4fda43de23d65405a3c90b924bc4a5c84753e388589d4ca343d9ba561a1d`.
- Local `snapcraft --use-lxd` succeeded despite reported remote infrastructure
  trouble. Packed metadata: 9.16.0, core24, strict, grade stable.
- Artifact: `calibre_9.16.0_amd64.snap`; SHA-256:
  `621ffeabdbc53ab7332d3b6925cf6ce37618c99057f9ce6a4e7012e36bd825ca`.
- Four packaging tests passed. Installed locally without sudo. Full smoke script
  passed HTML→EPUB, EPUB→old/both MOBI, EPUB→PDF and database import/list.
- Manager and EPUB viewer launched and rendered using disposable test data at
  `~/calibre-snap-smoke.CApUlQ/`. Personal libraries were not opened for this test.
  Known raw-usb scanner and nonfatal Chromium/GPU warnings remain.
- Uploaded with `snapcraft upload calibre_9.16.0_amd64.snap --release=candidate`.
  Store accepted **revision 3** and confirmed its release to **candidate**.
  Stable remains 9.15.0 revision 2; no stable promotion was requested.
- Build/runtime logs and screenshot: `artifacts/release-9.16.0/` (ignored).
- Local installation is the sideloaded 9.16.0 test build. This is not a full
  cross-version migration or hardware compatibility test. Await user testing
  before any stable promotion.

## Historical baseline: identity and publication

- Repository: https://github.com/popey/calibre-snap, branch `main`.
- Snap name and command: `calibre`. The directory is still named
  `CalibreUnofficial`; that is not the package name.
- Community-maintained packaging, not endorsed or supported by upstream.
  Direct snap issues to https://github.com/popey/calibre-snap/issues first.
- Calibre version currently pinned: **9.15.0**, upstream release 2026-09-18.
- Store revision **1** was uploaded with `grade: devel` and cannot go to stable.
- Rebuilt with `grade: stable`; Store revision **2** passed processing and was
  ready to release. The user subsequently confirmed releasing it.
- Revision 2 artifact: `calibre_9.15.0_amd64.snap`, SHA-256
  `443e535c7cfaa5e1abf99b4827e4190dcb5bd8306c35d080ad94fc569205145c`.
- Last pushed implementation commit: `721d3e3`, fixing LXD networking in CI.
  Initial repository commit: `16029db`.

## Packaging decisions and runtime fixes

`snap/snapcraft.yaml` uses core24, strict confinement, stable grade, amd64 only,
and LZO compression. It repackages the official Linux binary bundle; it does not
compile Calibre itself. The archive URL and SHA-256 are pinned together.
The GNOME extension provides desktop/GPU integration; upstream supplies Qt/Python.

`snap/local/bin/calibre-env` contains necessary runtime workarounds:

- Short `LD_LIBRARY_PATH`: the upstream native launcher has a fixed-size buffer
  and rejects the longer extension-generated path. Upstream adds its own libs.
- Configuration in `$SNAP_USER_DATA/config`; caches and conversion temporary
  files in `$SNAP_USER_COMMON/.cache` and its `tmp` subdirectory.
- Default `QT_QPA_PLATFORM=xcb`, allowing an explicit override; Fusion styling.
- Qt WebEngine's internal sandbox disabled; snap confinement remains strict.
  `--disable-dev-shm-usage` avoids incompatible shared-memory file locations.
- `LD_PRELOAD` loads the compiled socket compatibility adapter.

`snap/socket-compat/socket-compat.c` prefixes Calibre abstract Unix socket names
with `snap.calibre.` for snapd's namespace policy, for both bind and connect.
It leaves unrelated socket names alone. Tests exercise actual socket connections.
Native and snap Calibre therefore do **not** share the usual single-instance
lock: never open the same live library in both installations concurrently.
Avoid running local calibredb maintenance while the snap GUI owns the library.

Commands: `calibre`, `calibre.ebook-viewer`, `calibre.ebook-convert`,
`calibre.calibredb`. No generic ebook-convert/calibredb aliases are installed.
Use `snap run calibre` explicitly if a native installation shadows the command.

## Interfaces and known limits

- Audio playback connects automatically for manager and viewer.
- `raw-usb`, `removable-media`, and cups were disconnected in local tests.
- Without raw-usb, the device-scanner thread logs permission denied for
  `/sys/bus/usb/devices`; library management and reading still work.
- Connect raw-usb for USB enumeration/access and removable-media for mounted
  paths under `/media`, `/run/media`, `/mnt`. A reader may need both. Mount with
  the host file manager first; these interfaces do not prove UDisks/MTP support.
- Normal home access excludes hidden directories. Keep libraries in an ordinary
  non-hidden home folder, preferably outside snap revision data.
- Real reader transfers/eject, speech, IMEs, native Wayland, NVIDIA, printing,
  third-party plugins, content-server LAN discovery and trash recovery remain
  unverified. Host Wine/external helpers are not automatically accessible.
- Snapcraft reports optional Qt plugin dependencies and unused libraries.
  Do not assume optional features work, or suppress warnings without diagnosis.

The [Flatpak issue audit](flatpak-issue-audit.md) covers all 79 issues reviewed
on September 24, grouped by cause, with sources, mitigations and remaining tests.

## Validation completed

- Repeated local builds with `snapcraft --use-lxd` and installed-snap testing.
- Four packaging unit tests; both workflow files passed actionlint 1.7.7.
- HTML→EPUB, EPUB→old/both MOBI, EPUB→PDF and database import/list passed.
- Main GUI and standalone EPUB viewer rendered, including page navigation.
- Verified HTTPS returned 200; bundled Qt/PIL/zeroconf/SSL imports passed;
  12 Liberation font files found; disk-backed temp directory verified.
- Direct snap xdg-open hand-off reached the host chooser and Document Viewer
  rendered a generated PDF. Calibre's Qt PDF action and reader-position
  persistence are not covered by that test.
- Stable-grade rebuild repeated conversion/database smoke tests before upload.

Detailed records: [original validation](validation.md),
[migration](migration.md), [September 25 retest](retest-2026-09-25.md).

### Migration findings

An isolated official 9.15.0 binary installation imported the user's 12 source
files; the welcome guide gives 13 library records. The initial clean-install
migration used the former `calibre-unofficial` name. Later tests refreshed the
renamed snap and used a fresh full-library copy, not an empty snap profile.

Backups were restored and hash-verified. All 13 metadata records and 25 ebook/
cover files matched after copying. SQLite integrity checks passed. A custom
column edit stayed in the snap copy, and real EPUB/PDF conversion succeeded.
The 12 original source files were unchanged.

On September 25 the native library already differed from the older baseline;
its current state was backed up rather than overwritten. A native calibredb
reopen changed metadata.db by moving book 4's pending row from
`annotations_dirtied` to `metadata_dirtied`. Native-only reproduction on another
restoration produced the exact same SQL state. Other SQL content and all eight
native preference files were unchanged. A native read is not necessarily
byte-preserving. Do not restore an older backup over subsequent user edits.

Ubuntu's older deb → snap migration, full preference/plugin migration and
cross-version upgrade/rollback have not been demonstrated.

## GitHub automation

- `.github/workflows/build.yml`: main pushes, PRs and manual runs.
- `.github/workflows/sync-version-with-upstream.yml`: daily **06:23 UTC**, plus
  manual runs; restricted to `popey/calibre-snap`.
- `scripts/update-upstream.py` checks the latest stable GitHub release in
  `kovidgoyal/calibre`. It updates version, amd64 archive URL and checksum
  together. Rejects prereleases, downgrades, unexpected URLs, missing digests,
  and changed assets for an already pinned version.
- A newer version is built and smoke-tested before creating/updating a PR on
  `auto-update-calibre`. Only `snap/snapcraft.yaml` is committed by the bot.
- Uses `GITHUB_TOKEN`, with contents/PR write permissions; no PAT is required.
  The user confirmed enabling Actions' create/approve-PR setting.
- Nothing automatically merges or uploads/releases to the Store. After a
  maintainer reviews/merges an update, publication remains a separate step.
- The common build action initializes LXD and sets
  `sudo iptables -P FORWARD ACCEPT` on the disposable GitHub runner, matching
  Canonical's action. Without it the first CI run failed with network access
  errors during environment setup. Do not apply this CI firewall change casually
  to the user's workstation.
- Successful full CI build:
  https://github.com/popey/calibre-snap/actions/runs/36185266265
- Successful manually dispatched updater (9.15.0 already current):
  https://github.com/popey/calibre-snap/actions/runs/36184793588
- The initial no-update branch passed remotely. PR #1 subsequently updated
  Calibre to 9.16.0 and was merged; see the October update above. Snap, manifest
  and app-test evidence artifacts are retained for 14 days.

As checked September 27, recent upstream releases were usually 2–3 weeks apart,
mostly Fridays, with 1–4 week gaps. This is observed cadence, not a schedule:
https://calibre-ebook.com/whats-new . Daily checking is sufficient.

## Store text and artwork

- `store-assets/description.md`: paste-ready Store Markdown with the independent
  maintainer notice, issue tracker, raw-usb/removable-media commands and migration
  advice. The user requested a local file to paste into the web UI; its live
  publication has not been confirmed.
- `store-assets/calibre.svg`: upstream vector icon, explicitly **512×512**;
  retained 1024×1024 viewBox preserves scalable artwork. Source in asset README.
- Three direct app captures, **1600×900 PNGs**, under `store-assets/screenshots/`:
  cover library, Pride and Prejudice reader, metadata editor. No personal books
  or desktop chrome appear. Sources/attribution are in `store-assets/README.md`.
- Screenshot demo library: `artifacts/store-demo/Classics/`, seven Standard Ebooks
  classics. Download URLs need `?source=download` to return an EPUB instead of
  an intermediate HTML page; validate ZIP format before importing.
- `artifacts/store-demo/Library/` was an unsuccessful first import of those HTML
  landing pages; use `Classics/`, not that abandoned test library.

## Local data and working practices

The .gitignore excludes `*.snap`, build outputs, `artifacts/`, `migration-test/`,
and `library/`. Never commit downloaded personal books or test library data.

- `library/ebooks/`: user-supplied source books; preserve unchanged.
- `migration-test/upstream-library/`, `upstream-config/`: native test data.
- `migration-test/backups/`: initial backup; `restore-check/`: its restoration.
- `migration-test/retest-2026-09-25/`: later backup, restoration, copy, native-only
  control and reports. `before.tar` preserves that day's original state.
- `scripts/upstream-calibre.sh`: launches isolated official binary installation.
- `scripts/tree-checksums.py`: records/verifies file and symlink inventories.
- `artifacts/`: local logs, screenshots and probes, including confinement checks.
- Older `calibre-unofficial` artifacts/data may still exist. It is a separate
  snap; do not delete it or migrate settings implicitly.
- The user has authorized host snap operations without sudo after snap login:
  use `snap install`/`snap connect` locally. CI legitimately uses sudo.
- Close the GUI gracefully before replacement installs, for example
  `env DISPLAY=:0 calibre --shutdown-running-calibre`.

Typical local verification:

```sh
python3 -m unittest discover -s tests -v
snapcraft --use-lxd
snap install --dangerous ./calibre_9.15.0_amd64.snap
./scripts/smoke-test.sh
```

Socket tests, snap/LXD operations and GUI launches may require execution outside
the coding sandbox. A sandbox permission failure is not automatically an app bug.
Read the snap-packaging skill before packaging or publication work.

The handover, AGENTS.md and Store-description changes were committed and pushed
on October 11 together with the automated desktop tests. The description was
prepared for manual pasting into the Store UI; publication of that text remains
unconfirmed.
