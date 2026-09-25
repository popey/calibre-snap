#!/bin/sh
# Keep test data inside the invoking user's home, accessible through snap's home plug.
set -eu
work=$(mktemp -d "$HOME/calibre-snap-smoke.XXXXXX")
printf '<html><head><title>Calibre Snap Test</title></head><body><h1>Calibre Snap Test</h1><p>A sample ebook for the unofficial snap.</p></body></html>\n' > "$work/input.html"
calibre.calibredb --version
QT_QPA_PLATFORM=offscreen calibre.ebook-convert "$work/input.html" "$work/output.epub"
test -s "$work/output.epub"
# Flatpak #30 exposed failures in old/both MOBI and the PDF renderer.
for kind in old both; do
  QT_QPA_PLATFORM=offscreen calibre.ebook-convert "$work/output.epub" "$work/$kind.mobi" --mobi-file-type "$kind"
  test -s "$work/$kind.mobi"
done
QT_QPA_PLATFORM=offscreen calibre.ebook-convert "$work/output.epub" "$work/output.pdf"
test -s "$work/output.pdf"
calibre.calibredb add --with-library "$work/library" "$work/output.epub"
calibre.calibredb list --with-library "$work/library"
printf 'Smoke test passed. Test files and library: %s\n' "$work"
