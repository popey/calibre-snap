# Project context

Read [docs/handover.md](docs/handover.md) for the recorded project state,
packaging workarounds, release history, validation evidence and pending work.
The active repository is `popey/calibre-snap`; the snap name is `calibre`.

Preserve the user's books and library data. `library/`, `migration-test/` and
`artifacts/` are local, ignored data; never commit their contents. Use independent
library copies for migration tests and never open the same library concurrently
in native and snap Calibre.

For local snap operations, the user has already logged in and prefers commands
without sudo. Keep sudo in GitHub runner setup where required.
