# Calibre Flatpak issue audit — 2026-09-24

Reviewed all **79 non-PR issues**, open and closed, returned by the
[Flathub Calibre issue tracker](https://github.com/flathub/com.calibre_ebook.calibre/issues),
including maintainer follow-ups and the current manifest. Duplicate symptoms are
grouped below; every issue is linked. Closed is not treated as proof that a snap
is unaffected. Status distinguishes observed results, code-level assessment and
remaining tests. Historical failures are not automatically present in Calibre 9.15.

The current [Flatpak manifest](https://github.com/flathub/com.calibre_ebook.calibre/blob/master/com.calibre_ebook.calibre.yaml)
grants host filesystem/device access, UDisks D-Bus access, audio and desktop trash
access. The strict snap has materially different boundaries; copying Flatpak
permissions wholesale would not establish compatibility.

## Findings by generic issue

| Area / source issues | Snap assessment | Evidence, mitigation and remaining work |
| --- | --- | --- |
| Audio and read aloud: [#250](https://github.com/flathub/com.calibre_ebook.calibre/issues/250), [#151](https://github.com/flathub/com.calibre_ebook.calibre/issues/151) | **Applies; packaging gap addressed** | Added audio-playback to manager and viewer. The old package lacked it. Actual Piper voice download/speech and legacy speech-dispatcher integration remain untested; audio access alone is not a TTS guarantee. |
| External readers and reading position: [#265](https://github.com/flathub/com.calibre_ebook.calibre/issues/265), [#171](https://github.com/flathub/com.calibre_ebook.calibre/issues/171), [#63](https://github.com/flathub/com.calibre_ebook.calibre/issues/63) | **Partly tested; reader-specific behavior remains** | The snap uses /usr/bin/xdg-open → snapctl user-open, rather than executing arbitrary host apps. The snap’s xdg-open reached the host chooser and Document Viewer rendered the generated PDF. Calibre’s own Qt PDF launch path and external readers’ page-position persistence still need explicit tests. #265 concerns PDF/comic readers, not evidence that every internal EPUB bookmark fails. |
| Temporary storage and conversion: [#181](https://github.com/flathub/com.calibre_ebook.calibre/issues/181), [#30](https://github.com/flathub/com.calibre_ebook.calibre/issues/30) | **Applies; preventive change plus regression tests** | #181 is ENOSPC, not inherently a permissions failure. Explicit CALIBRE_TEMP_DIR now uses SNAP_USER_COMMON/.cache/tmp on disk. There is no promise against disk exhaustion. #30 was fixed in upstream 4.10.1; expanded smoke tests cover old/both MOBI and PDF output in addition to EPUB. |
| USB readers, mounted volumes and UDisks: [#13](https://github.com/flathub/com.calibre_ebook.calibre/issues/13), [#9](https://github.com/flathub/com.calibre_ebook.calibre/issues/9) | **Applies; unresolved hardware coverage** | raw-usb enables enumeration/access; removable-media enables mounted paths. Neither guarantees that Calibre can request host UDisks mounting, or that MTP works. Mount with the host first, then connect required plugs. No real Kobo/Kindle/MTP transfer is certified. |
| Plugins and external executables: [#189](https://github.com/flathub/com.calibre_ebook.calibre/issues/189), [#161](https://github.com/flathub/com.calibre_ebook.calibre/issues/161), [#157](https://github.com/flathub/com.calibre_ebook.calibre/issues/157), [#122](https://github.com/flathub/com.calibre_ebook.calibre/issues/122), [#18](https://github.com/flathub/com.calibre_ebook.calibre/issues/18) | **Applies; explicit compatibility limits** | The bundle has OpenSSL 3, but old oscrypto/plugin version parsers can still fail. Old Python/Qt plugin imports (#161/#157) require updated plugins, not weaker confinement. Host Wine is absent (#122); hidden Wine profiles and external helper executables are not automatically reachable. #18 additionally needs removable-media. No third-party plugin is certified. |
| TLS / certificate discovery: [#89](https://github.com/flathub/com.calibre_ebook.calibre/issues/89), [#6](https://github.com/flathub/com.calibre_ebook.calibre/issues/6) | **Probe passed on this host** | Verified HTTPS GET to calibre-ebook.com returned 200 through the bundled Python in the installed snap. Does not certify corporate/private CA roots, every metadata provider, or plugin-specific certificate handling. Do not disable TLS verification as a workaround. |
| mDNS / content-server discovery: [#299](https://github.com/flathub/com.calibre_ebook.calibre/issues/299) | **Reported cause absent; discovery unverified** | Reporter confirmed they were using the Fedora Flatpak; Flathub was unaffected. zeroconf imports in this snap. network and network-bind are present on the manager; actual LAN announcement, firewall behavior and remote discovery are not proven by an import test. |
| Wayland, XWayland and graphics: [#293](https://github.com/flathub/com.calibre_ebook.calibre/issues/293), [#158](https://github.com/flathub/com.calibre_ebook.calibre/issues/158), [#120](https://github.com/flathub/com.calibre_ebook.calibre/issues/120), [#57](https://github.com/flathub/com.calibre_ebook.calibre/issues/57), [#29](https://github.com/flathub/com.calibre_ebook.calibre/issues/29), [#26](https://github.com/flathub/com.calibre_ebook.calibre/issues/26) | **Applies; limited platform coverage** | X11 manager/viewer rendering passed locally. Default xcb requires X11 or XWayland; #293 demonstrates that forcing xcb can fail where that path is unavailable. QT_QPA_PLATFORM=wayland can be selected, but native Wayland, fractional scaling and other GPU/NVIDIA combinations remain untested. Keep the gpu-2404 integration and bundled Qt separate. |
| Native ABI and missing dependencies: [#225](https://github.com/flathub/com.calibre_ebook.calibre/issues/225), [#195](https://github.com/flathub/com.calibre_ebook.calibre/issues/195), [#119](https://github.com/flathub/com.calibre_ebook.calibre/issues/119) | **Relevant release-regression risk** | Bundled PIL.Image/Qt imports, 12 Liberation font files, and desktop startup passed in the renamed snap. Fonts are not replaced with Flatpak runtime symlinks (#119). Short LD_LIBRARY_PATH avoids the native launcher length limit, but does not prove #195’s exact cause. Preserve visible Snapcraft optional-plugin warnings and rebuild/test each update. |
| Themes, fonts, decorations and icons in dialogs: [#236](https://github.com/flathub/com.calibre_ebook.calibre/issues/236), [#153](https://github.com/flathub/com.calibre_ebook.calibre/issues/153), [#132](https://github.com/flathub/com.calibre_ebook.calibre/issues/132), [#34](https://github.com/flathub/com.calibre_ebook.calibre/issues/34), [#19](https://github.com/flathub/com.calibre_ebook.calibre/issues/19), [#16](https://github.com/flathub/com.calibre_ebook.calibre/issues/16), [#3](https://github.com/flathub/com.calibre_ebook.calibre/issues/3), [#2](https://github.com/flathub/com.calibre_ebook.calibre/issues/2) | **Applies; intentionally limited integration** | Fusion is selected; matching every host Qt/GTK theme is not promised. Loading host Qt theme plugins into the bundled Qt risks ABI mismatch. Host fonts, dark palette, title-button placement and cursor scaling vary by desktop. Local dialogs render, but CJK fonts, all themes and scaling are not certified. |
| Input methods: [#126](https://github.com/flathub/com.calibre_ebook.calibre/issues/126) | **Applies; untested with real IME** | Bundle includes IBus and compose input-context plugins, not an Fcitx plugin. Flatpak discussion reports QT_IM_MODULE=ibus as an Fcitx5 bridge, with scaling limitations. GNOME desktop integration does not itself prove CJK composition works; test actual IBus/Fcitx5 input on X11 and Wayland before claiming support. |
| Import, migration and library locations: [#101](https://github.com/flathub/com.calibre_ebook.calibre/issues/101), [#39](https://github.com/flathub/com.calibre_ebook.calibre/issues/39), [#104](https://github.com/flathub/com.calibre_ebook.calibre/issues/104) | **Partly tested; documented restrictions** | The 12 supplied files imported; copied-library migration preserved all 13 records, custom metadata and 25 ebook/cover files. Source files/configuration remained intact. Fresh snap settings do not auto-import native settings. home excludes hidden locations; removable/media/network mounts require appropriate access. Choose a literal external home-directory library path, not an unexpanded ${XDG_DATA_HOME} string or snap revision data. |
| Trash and deletion: [#83](https://github.com/flathub/com.calibre_ebook.calibre/issues/83) | **Applies; recovery test outstanding** | Do not assume sandbox deletions appear in the host desktop trash. Calibre’s own recently-deleted-book handling and snap-local XDG trash need explicit delete/restore/space-reclamation testing on disposable data. Never make broad host-trash access the default just to hide this difference. |
| Permission breadth: [#186](https://github.com/flathub/com.calibre_ebook.calibre/issues/186), [#51](https://github.com/flathub/com.calibre_ebook.calibre/issues/51) | **Different implementation; still a trust decision** | Strict confinement is retained, with home/network and optional raw-usb/removable-media. It does not expose all host devices/files as the Flatpak manifest does. home still permits substantial user-file access, and installed plugins inherit the app’s permissions. |
| Desktop IDs, dock grouping and MIME metadata: [#216](https://github.com/flathub/com.calibre_ebook.calibre/issues/216), [#114](https://github.com/flathub/com.calibre_ebook.calibre/issues/114), [#69](https://github.com/flathub/com.calibre_ebook.calibre/issues/69), [#38](https://github.com/flathub/com.calibre_ebook.calibre/issues/38), [#20](https://github.com/flathub/com.calibre_ebook.calibre/issues/20), [#21](https://github.com/flathub/com.calibre_ebook.calibre/issues/21), [#4](https://github.com/flathub/com.calibre_ebook.calibre/issues/4), [#1](https://github.com/flathub/com.calibre_ebook.calibre/issues/1) | **Partly addressed; packaging-system differences** | Added StartupWMClass=calibre and renamed the manager desktop file/Exec consistently. Notification, editor/viewer dock identity and native Wayland IDs need further work/testing; there are not yet separate viewer/editor desktop launchers. Flathub AppStream/catalog/ODRS-specific faults do not directly carry over to Snap Store metadata. |
| Command-line entry points: [#25](https://github.com/flathub/com.calibre_ebook.calibre/issues/25), [#7](https://github.com/flathub/com.calibre_ebook.calibre/issues/7) | **Addressed** | Use calibre.ebook-convert, calibre.calibredb and calibre.ebook-viewer, not paths inside /snap/<name>/<revision>/opt. No generic ebook-convert alias is installed, so native tools are not silently replaced. The main calibre command may coexist with a native calibre earlier/later in PATH; use snap run calibre to select this snap explicitly. |
| Runtime directory and startup performance: [#50](https://github.com/flathub/com.calibre_ebook.calibre/issues/50), [#24](https://github.com/flathub/com.calibre_ebook.calibre/issues/24) | **Potential host integration/performance risk** | Desktop extension handles runtime directory setup; local launch worked. Do not chmod the host /run/user directory to work around failures. LZO reduces decompression cost, but no comparative startup benchmark has been run; cold launch/font-cache creation can differ. |
| Native update notification: [#221](https://github.com/flathub/com.calibre_ebook.calibre/issues/221) | **Applies; documented behavior** | Calibre can announce upstream updates before the snap recipe is updated. That notification does not refresh the snap. calibre --no-update-check suppresses it if desired; the automated PR workflow handles packaging updates. Store refresh automation is not configured yet. |
| Architecture support: [#107](https://github.com/flathub/com.calibre_ebook.calibre/issues/107) | **Known gap** | Only amd64 is declared and locally tested. Upstream supplies arm64, but it requires a separate recipe checksum path, build matrix and runtime test before enabling. |
| Building from source versus upstream bundle: [#17](https://github.com/flathub/com.calibre_ebook.calibre/issues/17) | **Applies as a packaging tradeoff** | This snap repackages the official binary bundle, verified by SHA-256, and compiles only its socket adapter. It does not claim to compile Calibre or receive upstream support for sandbox-specific problems. Runtime tests are required despite the bundled dependencies. |
| Update lag, version reporting and changelogs: [#301](https://github.com/flathub/com.calibre_ebook.calibre/issues/301), [#291](https://github.com/flathub/com.calibre_ebook.calibre/issues/291), [#277](https://github.com/flathub/com.calibre_ebook.calibre/issues/277), [#261](https://github.com/flathub/com.calibre_ebook.calibre/issues/261), [#256](https://github.com/flathub/com.calibre_ebook.calibre/issues/256), [#253](https://github.com/flathub/com.calibre_ebook.calibre/issues/253), [#222](https://github.com/flathub/com.calibre_ebook.calibre/issues/222), [#203](https://github.com/flathub/com.calibre_ebook.calibre/issues/203), [#179](https://github.com/flathub/com.calibre_ebook.calibre/issues/179), [#133](https://github.com/flathub/com.calibre_ebook.calibre/issues/133), [#27](https://github.com/flathub/com.calibre_ebook.calibre/issues/27), [#22](https://github.com/flathub/com.calibre_ebook.calibre/issues/22), [#12](https://github.com/flathub/com.calibre_ebook.calibre/issues/12), [#152](https://github.com/flathub/com.calibre_ebook.calibre/issues/152), [#192](https://github.com/flathub/com.calibre_ebook.calibre/issues/192) | **Automation added; human/release work remains** | Daily newer-version check opens/updates one PR only after building/testing the pinned archive. PR links upstream notes and validation artifacts. A maintainer must still review/merge and publish: merely filing PRs does not solve #277’s unmerged-update backlog. No Store release is implied. |
| Flatpak infrastructure, verification and runtime maintenance: [#304](https://github.com/flathub/com.calibre_ebook.calibre/issues/304), [#284](https://github.com/flathub/com.calibre_ebook.calibre/issues/284), [#278](https://github.com/flathub/com.calibre_ebook.calibre/issues/278), [#227](https://github.com/flathub/com.calibre_ebook.calibre/issues/227), [#164](https://github.com/flathub/com.calibre_ebook.calibre/issues/164), [#209](https://github.com/flathub/com.calibre_ebook.calibre/issues/209), [#23](https://github.com/flathub/com.calibre_ebook.calibre/issues/23), [#276](https://github.com/flathub/com.calibre_ebook.calibre/issues/276) | **Mechanisms mostly Flatpak-specific** | OSTree static deltas, Flathub verification/catalog and freedesktop SDK/AppStream tooling do not apply directly. Network/cache/build failures and runtime lifecycle still apply in general; Actions build failures remain visible. An unofficial snap does not acquire upstream endorsement by using the calibre name. |

## Changes made in response

- Added `audio-playback` to the manager and viewer.
- Set `CALIBRE_TEMP_DIR` to `$SNAP_USER_COMMON/.cache/tmp` (created by the wrapper).
- Added `StartupWMClass=calibre`.
- Extended installed-snap CI conversion coverage to old/both MOBI and PDF output.
- Added the build-before-PR upstream checker with version/URL/hash validation.
- Renamed snap/app/desktop/socket namespace and tests to `calibre`; older snap
  validation documents deliberately retain their historical name and paths.

## Priority follow-up tests

1. Real mounted Kobo/Kindle/MTP transfer, reconnect and eject; UDisks-mediated mounting.
2. Calibre’s PDF/comic launch path, reading-position persistence and other host-reader combinations.
3. Piper speech/voice download, real IBus/Fcitx5 composition, native Wayland and NVIDIA.
4. Representative current plugins with native dependencies; expected failure of host-only helpers.
5. Disposable-book deletion, restore and cache/trash cleanup; content server plus LAN discovery.

These are follow-ups, not claims of functionality. Keep migration copies/backups
and do not run native and snap Calibre against the same live library.

## Renamed snap validation

Built with `snapcraft --use-lxd`, installed with `snap install --dangerous`, and
launched as `calibre` on this Ubuntu 24.04 X11 desktop on 2026-09-24.
Artifact: `calibre_9.15.0_amd64.snap`; SHA-256:
`95c99da3db1f0e6c9166f8fb2fd7d06b39f15caa97b423668059e8f1c2ade3cc`.

- Manager completed first-run setup and displayed the disposable smoke-test library.
- HTML→EPUB, EPUB→old MOBI, EPUB→both MOBI, EPUB→PDF and database import/list passed.
- The headless PDF conversion emitted GPU/Vulkan and confined Chromium
  NETLINK/OOM-adjustment warnings but completed and produced a readable PDF.
- The snap's external opener presented the host application chooser; selecting
  Document Viewer opened and rendered that PDF. This tested the opener directly,
  not Calibre's Qt PDF action or reading-position persistence.
- Verified HTTPS returned 200; zeroconf, PIL.Image and Qt imports passed; 12 bundled
  Liberation font files were present.
- Temporary files resolved under `~/snap/calibre/common/.cache/tmp`;
  `audio-playback` was connected automatically.
- With `raw-usb` disconnected, the device-scanner thread still reports permission
  denied on `/sys/bus/usb/devices`; the manager remains usable. Hardware transfer
  support is not established by this launch.
- Packaging unit tests (four) and workflow actionlint passed. The live upstream
  checker reported 9.15.0 already current. Remote PR creation awaits deployment
  of the repository/workflows and the documented Actions permission setting.

Test data was generated in `~/calibre-snap-smoke.yjMBNn`; the supplied books and
native migration-test library were not used for these writes. The older
`calibre-unofficial` snap was retained as a separate installation.
