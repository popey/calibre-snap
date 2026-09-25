# Migration test and recommended library migration

The current package is `calibre`. The dated results below used the former
`calibre-unofficial` name; those data paths are historical.

Use a **copy of the complete library**, not a re-import of its book files. The
library contains `metadata.db`, covers, metadata backups, and other state.
Re-importing EPUB/PDF files alone will not preserve all Calibre metadata.

1. Close Calibre, its viewer, calibredb, and any content server. Do this for both
   installations before copying anything.
2. Back up the complete original library and Calibre configuration directory.
   Verify the backup by restoring it elsewhere and comparing file checksums.
3. Copy the original library into a new, non-hidden folder below your home
   directory. Do not use hard links or symlinks to the original library.
4. Install the snap. On first launch, choose the **copied library** in the welcome
   wizard. If already configured, use Switch/create library → use an existing
   library at the new location.
5. Compare book counts, metadata, custom columns, covers, and ebook checksums.
   Open representative formats, then make a test edit only in the copied library.
6. Close the snap and confirm that the original library still works in the
   upstream application. Keep the original and backup until satisfied.

This initial route uses fresh snap preferences. Configuration is backed up for
rollback; it is not blindly copied into the snap. Old settings can contain
absolute library paths and plugins with different filesystem requirements.
Full preference/plugin migration is a separate test.

Do not open the **same library directory** in upstream Calibre and the snap at
once. The snap's compatibility adapter changes the abstract socket namespace,
so their usual single-instance locks do not coordinate across installations.
Also avoid pointing an older Calibre at a library modified by a newer version;
keep the original copy for rollback.

Upstream's supported data transfer feature is described in its
[FAQ](https://manual.calibre-ebook.com/faq.html#how-do-i-move-my-calibre-data-from-one-computer-to-another).
This test exercises full-directory copying with fresh snap settings.

## Local test layout

- `library/ebooks/`: supplied source books; never edited.
- `migration-test/upstream-9.15.0/`: official Linux binary bundle.
- `migration-test/runtime/`: private Ubuntu libxcb-cursor0 dependency.
- `migration-test/upstream-config/`: independent upstream preferences.
- `migration-test/upstream-library/`: original imported library.
- `migration-test/snap-library/`: independent library copy for the snap.
- `migration-test/backups/upstream-before-snap.tar`: library and config backup.
- `migration-test/restore-check/`: verified restoration of that backup.
- `migration-test/reports/`: checksums, metadata, and results.

Launch the original installation with `./scripts/upstream-calibre.sh`. Its
configuration and cache are isolated; it does not depend on the snap, modify
system command aliases, or register desktop/MIME defaults. This means the first
test covers an isolated official binary install, not Ubuntu's older deb package
or a system-wide upstream postinstall setup.

## Results — 2026-09-24

**Passed for official binary 9.15.0 → snap 9.15.0 (amd64/core24).**

- Imported all 12 supplied files (EPUB, PDF, MOBI, ZIP). The upstream welcome
  wizard added its Quick Start Guide, giving 13 library records.
- Verified an actual backup restoration: 41 library files and 6 configuration
  files matched the pre-migration SHA-256 inventories.
- The previous snap was already uninstalled before this test. Snapd reported no
  installed Calibre snap, no saved snapshots, and no Calibre snap user-data
  directory. A fresh installation of the built artifact succeeded.
- Installation left the source library, source configuration, and all 12 supplied
  files unchanged. Fresh first-run setup created a separate library and settings.
- Opened the complete copied library in the snap. All 13 records matched in every
  exported metadata field after normalizing the different library paths,
  including UUIDs, tags, identifiers, timestamps, and the test custom field.
- All 25 ebook and cover files in the migrated copy matched the original hashes.
  SQLite integrity checks passed on original, migrated, and restored databases.
- Changed the custom field on book 1 only in the snap copy. All original library
  and configuration file hashes still matched. Upstream's calibredb reopened the
  original and returned exactly the baseline metadata and original custom value.
- Converted a supplied EPUB and PDF from the migrated copy to non-empty text
  output successfully. The supplied files themselves remained unchanged.
- Reopened the original library in the independent upstream GUI successfully.

### Findings

- The clean snap defaults to `~/snap/calibre-unofficial/<revision>/Calibre Library`.
  For migration, deliberately choose an external home-directory copy instead.
  A library inside snap user data is subject to snap data lifecycle/removal.
- The wizard's displayed path is not directly editable: use its **Change** button,
  the Switch/create library action, or the tested explicit launch command:

  ```sh
  calibre --with-library "$PWD/migration-test/snap-library"
  ```

- The raw-usb connection is absent on a fresh install. The GUI/library functions
  worked, but its device-scanner thread logged a permission error. Connect it
  separately if USB enumeration is needed; no reader hardware was tested here.
- Sharing the original library between applications is not the tested migration
  route. Their snap/native socket namespaces differ; keep separate copies and
  close each application before maintenance or backup.

### Limits

This does not yet establish Ubuntu's **7.6.0 deb → 9.15.0 snap** compatibility,
full settings/plugin migration, system-wide desktop/MIME integration, PDF opening
in external desktop applications, device transfer, or snap refresh/rollback across
Calibre versions. EPUB/PDF conversion was tested; MOBI/ZIP preservation and metadata
were checked but their rendering was not. The original upstream installation uses
an isolated configuration rather than the user's default `~/.config/calibre`.

All supplied books, extracts, screenshots and local reports are excluded from git
under `library/` and `migration-test/`.
